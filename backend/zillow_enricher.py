"""
Property enrichment: given a property address, fetch property details via DuckDuckGo
and a Street View image via the Google Street View Static API.

Rate-limited to 1 request per 3 seconds. Results are cached in the DB.
"""
import asyncio
import logging
import os
import re
from typing import Optional, Dict

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

async def _fetch_property_data(address: str, city: str = "Spokane", state: str = "WA", fetch_estimate: bool = True, fetch_image: bool = True, fetch_apn: bool = True, zillow_url: Optional[str] = None) -> Dict:
    """Returns dict with image_url, estimated_value, and extended property details."""
    result = {
        "image_url": None, "zillow_url": zillow_url, "estimated_value": None,
        "bedrooms": None, "bathrooms": None, "square_feet": None,
        "lot_size": None, "property_type": None, "year_built": None, "apn": None
    }

    # 1. Fetch Property Value Estimate using DuckDuckGo HTML search
    if fetch_estimate:
        ddg_query = f"{address} {city} {state} zillow".replace(" ", "+")
        ddg_url = f"https://html.duckduckgo.com/html/?q={ddg_query}"
        try:
            # Run blocking requests.get in a separate thread so Uvicorn can still answer API polls
            req = await asyncio.to_thread(
                requests.get, ddg_url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}, timeout=10
            )
            soup = BeautifulSoup(req.text, 'html.parser')
            
            for res in soup.find_all('div', class_='result'):
                title_elem = res.find('h2', class_='result__title')
                desc_elem = res.find('a', class_='result__snippet')
            
                title = title_elem.text.strip() if title_elem else ""
                desc = desc_elem.text.strip() if desc_elem else ""
            
                combined = title + " " + desc
            
                # Value extraction
                if result["estimated_value"] is None:
                    zmatches = re.findall(r'(?:Zestimate|Estimated value|price.*?changed to|Est\. Value).*?\$([0-9,]+)', combined, re.IGNORECASE)
                    if zmatches:
                        val_str = zmatches[0].replace(',', '')
                        result["estimated_value"] = int(val_str)
            
                # Beds extraction
                if result["bedrooms"] is None:
                    beds_matches = re.findall(r'(\d+(?:\.\d+)?)\s*(?:bed|beds|bd|-bed)', combined, re.IGNORECASE)
                    if beds_matches:
                        result["bedrooms"] = float(beds_matches[0])
                    
                # Baths extraction
                if result["bathrooms"] is None:
                    baths_matches = re.findall(r'(\d+(?:\.\d+)?)\s*(?:bath|baths|ba|-bath)', combined, re.IGNORECASE)
                    if baths_matches:
                        result["bathrooms"] = float(baths_matches[0])
                    
                # Sqft extraction
                if result["square_feet"] is None:
                    sqft_matches = re.findall(r'([0-9,]+)\s*(?:sqft|sq\.?\s*ft\.?|square feet)', combined, re.IGNORECASE)
                    if sqft_matches:
                        result["square_feet"] = int(sqft_matches[0].replace(',', ''))
                    
                # Year Built extraction
                if result["year_built"] is None:
                    year_matches = re.findall(r'(?:built in|built|year built)\s*(\d{4})', combined, re.IGNORECASE)
                    if year_matches:
                        result["year_built"] = int(year_matches[0])
                    
                # Property Type extraction
                if result["property_type"] is None:
                    if re.search(r'single(\s|-)family', combined, re.IGNORECASE):
                        result["property_type"] = "Single Family"
                    elif re.search(r'condo', combined, re.IGNORECASE):
                        result["property_type"] = "Condominium"
                    elif re.search(r'townhouse|townhome', combined, re.IGNORECASE):
                        result["property_type"] = "Townhouse"
                    elif re.search(r'multi(\s|-)family|duplex|triplex|fourplex', combined, re.IGNORECASE):
                        result["property_type"] = "Multi-Family"
                    
                # Lot Size extraction
                if result["lot_size"] is None:
                    lot_matches = re.findall(r'(\d+(?:\.\d+)?)\s*(?:acres|acre lot|acre|sqft lot)', combined, re.IGNORECASE)
                    if lot_matches:
                        result["lot_size"] = f"{lot_matches[0]} Acres" if 'acre' in combined.lower() else f"{lot_matches[0]} sqft"
                    
                # Check if primary values are found to break early
                if result.get("estimated_value") and result.get("bedrooms") and result.get("bathrooms") and result.get("square_feet") and result.get("year_built"):
                    break
        except Exception as e:
            logger.warning(f"DDG estimate extraction error for '{address}': {e}")

    # 1.5 Fetch APN using specialized DDG query
    if fetch_apn:
        ddg_apn_query = f"{address} {city} {state} parcel number".replace(" ", "+")
        ddg_apn_url = f"https://html.duckduckgo.com/html/?q={ddg_apn_query}"
        try:
            req = await asyncio.to_thread(
                requests.get, ddg_apn_url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}, timeout=10
            )
            soup = BeautifulSoup(req.text, 'html.parser')
            
            for res in soup.find_all('div', class_='result'):
                desc_elem = res.find('a', class_='result__snippet')
                desc = desc_elem.text.strip() if desc_elem else ""
                
                apn_match = re.search(r'Parcel Number:\s*([a-zA-Z0-9.\-]+)', desc, re.IGNORECASE)
                if apn_match:
                    result["apn"] = apn_match.group(1)
                    break
        except Exception as e:
            logger.warning(f"DDG APN extraction error for '{address}': {e}")


    # 2. Build a Google Street View Static API URL for the property address.
    # Legitimate API call — no scraping, no bot detection, works reliably from VPS IPs.
    # Free tier: 25,000 requests/month. Image is served directly by Google on browser load.
    if fetch_image:
        try:
            api_key = os.environ.get("GOOGLE_STREET_VIEW_API_KEY", "AIzaSyBPrsUz1n4Y8DYC4lYzQntSFG0kSohuf_Y")
            location = f"{address}, {city}, {state}".replace(" ", "+")
            street_view_url = (
                f"https://maps.googleapis.com/maps/api/streetview"
                f"?size=640x480&location={location}&key={api_key}"
            )
            result["image_url"] = street_view_url
            logger.info(f"Built Street View URL for {address}")
        except Exception as e:
            logger.warning(f"Street View URL build failed for '{address}': {e}")

    return result

async def fetch_scout_data(apn: str) -> dict:
    """
    Fetch owner, assessed value, taxes, and last sale from Spokane County SCOUT.
    URL: https://cp.spokanecounty.org/scout/propertyinformation/Summary.aspx?PID={apn}
    Returns a dict with keys: owner_name, assessed_value, annual_taxes,
                               last_sale_price, last_sale_date
    Any field that cannot be parsed is left as None.
    """
    url = f"https://cp.spokanecounty.org/scout/propertyinformation/Summary.aspx?PID={apn}"
    result = {
        "owner_name": None,
        "assessed_value": None,
        "annual_taxes": None,
        "last_sale_price": None,
        "last_sale_date": None,
    }
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        resp = await asyncio.to_thread(requests.get, url, headers=headers, timeout=15)
        if resp.status_code != 200:
            logger.warning(f"SCOUT returned HTTP {resp.status_code} for APN {apn}")
            return result

        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text(" ", strip=True)

        # ── Owner Name ─────────────────────────────────────────────────────────
        # SCOUT renders owner in a <td> after a label containing "Owner"
        for row in soup.find_all("tr"):
            cells = row.find_all("td")
            for i, cell in enumerate(cells):
                label = cell.get_text(strip=True).lower()
                if "owner" in label and i + 1 < len(cells):
                    val = cells[i + 1].get_text(strip=True)
                    if val and len(val) > 2:
                        result["owner_name"] = val
                        break
            if result["owner_name"]:
                break

        # ── Assessed / Market Value ────────────────────────────────────────────
        # Look for "Total Assessed" or "Assessed Value" followed by a dollar amount
        m = re.search(
            r'(?:Total Assessed|Assessed Value|Market Value)[^\$]*\$\s*([\d,]+)',
            text, re.IGNORECASE
        )
        if m:
            result["assessed_value"] = int(m.group(1).replace(",", ""))

        # Fallback: any labelled row in tables
        if not result["assessed_value"]:
            for row in soup.find_all("tr"):
                cells = row.find_all("td")
                for i, cell in enumerate(cells):
                    label = cell.get_text(strip=True).lower()
                    if ("assessed" in label or "market value" in label) and i + 1 < len(cells):
                        val = cells[i + 1].get_text(strip=True).replace("$", "").replace(",", "").strip()
                        if val.isdigit():
                            result["assessed_value"] = int(val)
                            break
                if result["assessed_value"]:
                    break

        # ── Annual Property Taxes ──────────────────────────────────────────────
        m = re.search(
            r'(?:Annual Tax|Property Tax|Taxes?\s+Due|Current Year Tax)[^\$]*\$\s*([\d,]+)',
            text, re.IGNORECASE
        )
        if m:
            result["annual_taxes"] = int(m.group(1).replace(",", ""))

        # ── Last Sale Price ────────────────────────────────────────────────────
        m = re.search(
            r'(?:Last Sale|Sale Price|Transfer Amount|Sales Price)[^\$\d]*\$?\s*([\d,]+)',
            text, re.IGNORECASE
        )
        if m:
            raw = m.group(1).replace(",", "")
            if raw.isdigit() and int(raw) > 1000:
                result["last_sale_price"] = int(raw)

        # ── Last Sale Date ─────────────────────────────────────────────────────
        m = re.search(
            r'(?:Last Sale Date|Sale Date|Transfer Date)[^\d]*(\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})',
            text, re.IGNORECASE
        )
        if m:
            result["last_sale_date"] = m.group(1)

        logger.info(f"SCOUT fetch OK for APN {apn}: {result}")
    except Exception as e:
        logger.warning(f"SCOUT fetch error for APN {apn}: {e}")

    return result


async def enrich_properties_zillow(db_session, properties_to_enrich, status_dict=None):
    """
    Given a list of Property ORM objects missing image or estimate data,
    fetch data for each and update the DB.
    Rate-limited: 1 request per 3 seconds.
    """
    enriched = 0
    total = len(properties_to_enrich)
    for idx, prop in enumerate(properties_to_enrich):
        if status_dict is not None:
            status_dict["status_text"] = f"Enriching Data ({idx+1}/{total}): {prop.address}"
            
        needs_image = not prop.image_url
        needs_estimate = not prop.estimated_value or not prop.bedrooms or not prop.bathrooms or not prop.square_feet or not prop.year_built or not prop.property_type or not prop.lot_size
        needs_apn = not prop.apn
        needs_scout = prop.apn and not prop.scout_fetched_at

        if not needs_image and not needs_estimate and not needs_apn and not needs_scout:
            continue

        data = await _fetch_property_data(prop.address, prop.city, fetch_estimate=needs_estimate, fetch_image=needs_image, fetch_apn=needs_apn, zillow_url=prop.zillow_url)
        changed = False

        if data.get("image_url") and not prop.image_url:
            prop.image_url = data["image_url"]
            changed = True
            
        if data.get("estimated_value") and not prop.estimated_value:
            prop.estimated_value = data["estimated_value"]
            changed = True
            
        if data.get("bedrooms") and not prop.bedrooms:
            prop.bedrooms = data["bedrooms"]
            changed = True
            
        if data.get("bathrooms") and not prop.bathrooms:
            prop.bathrooms = data["bathrooms"]
            changed = True
            
        if data.get("square_feet") and not prop.square_feet:
            prop.square_feet = data["square_feet"]
            changed = True
            
        if data.get("lot_size") and not prop.lot_size:
            prop.lot_size = data["lot_size"]
            changed = True
            
        if data.get("property_type") and not prop.property_type:
            prop.property_type = data["property_type"]
            changed = True
            
        if data.get("year_built") and not prop.year_built:
            prop.year_built = data["year_built"]
            changed = True
            
        if data.get("apn") and not prop.apn:
            prop.apn = data["apn"]
            changed = True

        # ── Spokane County SCOUT data ──────────────────────────────────────────
        # Fetch on first enrichment pass once we have an APN (either existing or just discovered above)
        effective_apn = prop.apn or data.get("apn")
        if effective_apn and not prop.scout_fetched_at:
            scout = await fetch_scout_data(effective_apn)
            from datetime import datetime as dt
            prop.scout_fetched_at = dt.utcnow()
            if scout.get("owner_name"):
                prop.owner_name = scout["owner_name"]
            if scout.get("assessed_value"):
                prop.assessed_value = scout["assessed_value"]
            if scout.get("annual_taxes"):
                prop.annual_taxes = scout["annual_taxes"]
            if scout.get("last_sale_price"):
                prop.last_sale_price = scout["last_sale_price"]
            if scout.get("last_sale_date"):
                prop.last_sale_date = scout["last_sale_date"]
            changed = True
            await asyncio.sleep(1)   # be polite to the county server

        # Always set a fallback URL so we don't endlessly re-queue properties that Google/DDG cannot find
        if not prop.zillow_url:
            zillow_query = f"{prop.address}-{prop.city}-WA".replace(" ", "-").replace(",", "")
            prop.zillow_url = f"https://www.zillow.com/homes/{zillow_query}_rb/"
            changed = True

        if changed:
            enriched += 1
            db_session.add(prop)

        # Rate limit
        await asyncio.sleep(3)

    db_session.commit()
    logger.info(f"Property image enrichment complete: {enriched} properties updated")
    return enriched
