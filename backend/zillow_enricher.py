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
            api_key = os.environ.get("GOOGLE_STREET_VIEW_API_KEY", "")
            if not api_key:
                logger.warning("GOOGLE_STREET_VIEW_API_KEY not set — skipping Street View image")
            else:
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
    Full scrape of Spokane County SCOUT Summary page.
    URL: https://cp.spokanecounty.org/scout/propertyinformation/Summary.aspx?PID={apn}

    Returns a rich dict covering:
      owner_name, owner_address,
      assessed_value, assessed_land, assessed_building,
      annual_taxes, taxes_owing,
      last_sale_price, last_sale_date,
      scout_legal, scout_parcel_class, scout_tca, scout_land_sqft,
      scout_house_type, scout_basement_sqft, scout_garage_sqft,
      scout_sales  (JSON list of {date, price, instrument}),
      scout_permits (JSON list of {number, date, description})
    """
    import json as _json
    url = f"https://cp.spokanecounty.org/scout/propertyinformation/Summary.aspx?PID={apn}"
    result = {
        "owner_name": None, "owner_address": None,
        "assessed_value": None, "assessed_land": None, "assessed_building": None,
        "annual_taxes": None, "taxes_owing": None,
        "last_sale_price": None, "last_sale_date": None,
        "scout_legal": None, "scout_parcel_class": None, "scout_tca": None,
        "scout_land_sqft": None, "scout_house_type": None,
        "scout_basement_sqft": None, "scout_garage_sqft": None,
        "scout_sales": None, "scout_permits": None,
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
        full_text = soup.get_text(" ", strip=True)

        def _money(s):
            """Parse '$1,234,567' or '$29,122.00' or '1234567' -> int, or None."""
            s = re.sub(r'[,$\s]', '', s or '')
            try:
                return int(float(s)) if s else None
            except (ValueError, TypeError):
                return None

        def _table_rows(section_keyword):
            """Find all <tr> rows under the panel whose heading contains section_keyword."""
            for tag in soup.find_all(['h2','h3','h4','div','span','td','th']):
                if section_keyword.lower() in tag.get_text(strip=True).lower():
                    parent = tag.find_parent(['table','div','section','fieldset'])
                    if parent:
                        return parent.find_all('tr')
            return []

        # ── Owner ──────────────────────────────────────────────────────────────
        # SCOUT renders owner info as bold labels inside divs (not table cells):
        #   <strong>Owner Name:</strong> WILSON, ERIC A
        #   <strong>Address:</strong> 1759 EDGEFIELD LN, ...
        # Use regex on full_text which is more robust than table parsing.
        m = re.search(r'Owner Name:\s*([^\n]+?)(?=\s*Address:|\s*Taxpayer|\s*$)', full_text, re.IGNORECASE)
        if m:
            result["owner_name"] = m.group(1).strip()
        # Owner address: the "Address:" immediately following the owner block
        m = re.search(r'Owner Name:[^\n]+?Address:\s*([^\n]+?)(?=\s*Taxpayer|\s*$)', full_text, re.IGNORECASE | re.DOTALL)
        if m:
            result["owner_address"] = m.group(1).strip()

        # ── Site Address table: Land Size, Legal, Parcel Class, TCA ───────────
        # The table has a header row: Parcel Type | Site Address | City | Land Size | ...
        for table in soup.find_all("table"):
            headers_row = table.find("tr")
            if not headers_row:
                continue
            ths = [th.get_text(strip=True).lower() for th in headers_row.find_all(["th","td"])]
            if "land size" in ths or "size desc." in ths:
                data_rows = table.find_all("tr")[1:]
                for dr in data_rows:
                    cells = [td.get_text(strip=True) for td in dr.find_all("td")]
                    if not cells:
                        continue
                    def _col(name):
                        try:
                            idx = next(i for i,h in enumerate(ths) if name in h)
                            return cells[idx] if idx < len(cells) else None
                        except StopIteration:
                            return None
                    land_raw = _col("land size") or ""
                    m = re.search(r'([\d,]+)', land_raw)
                    if m:
                        result["scout_land_sqft"] = int(m.group(1).replace(",",""))
                    result["scout_parcel_class"] = _col("description") or _col("parcel class")
                    result["scout_tca"] = _col("tax code area") or _col("tca") or _col("tax code")
                    break

        # Legal description — appears as plain text after the table in that section
        m = re.search(r'([A-Z0-9 ]+(?:ADD|ADDITION|SUB|SUBDIVISION|BLOCK|LOT)[A-Z0-9 ]+(?:L\d+\s+B\d+)?)', full_text)
        if m:
            result["scout_legal"] = m.group(0).strip()

        # ── Assessed Values — parse the year-keyed table ───────────────────────
        # Columns: Tax Year | Taxable | Market Total | Land | Dwelling/Structure | ...
        for table in soup.find_all("table"):
            headers_row = table.find("tr")
            if not headers_row:
                continue
            ths = [th.get_text(strip=True).lower() for th in headers_row.find_all(["th","td"])]
            if "market total" in ths and "land" in ths:
                data_rows = table.find_all("tr")[1:]
                for dr in data_rows:
                    cells = [td.get_text(strip=True) for td in dr.find_all("td")]
                    if not cells:
                        continue
                    try:
                        mt_idx  = next(i for i,h in enumerate(ths) if "market total" in h)
                        land_idx= next(i for i,h in enumerate(ths) if h == "land")
                        dwell_idx=next(i for i,h in enumerate(ths) if "dwelling" in h or "structure" in h)
                        result["assessed_value"]    = _money(cells[mt_idx])
                        result["assessed_land"]     = _money(cells[land_idx])
                        result["assessed_building"] = _money(cells[dwell_idx])
                    except (StopIteration, IndexError):
                        pass
                    break   # only want first (most recent) data row
                break

        # ── Taxes ─────────────────────────────────────────────────────────────
        # "Total Charges Owing: $5,019.75"
        m = re.search(r'Total Charges Owing[:\s]*\$\s*([\d,]+\.?\d*)', full_text, re.IGNORECASE)
        if m:
            result["taxes_owing"] = float(m.group(1).replace(",", ""))

        # Annual tax for current year: first "Total Taxes for YYYY" row value
        m = re.search(r'Total Taxes for \d{4}\s+([\d,]+\.?\d*)', full_text)
        if m:
            result["annual_taxes"] = int(float(m.group(1).replace(",", "")))

        # ── Characteristics ────────────────────────────────────────────────────
        # Table columns: Dwelling | Year Built | Gross Living Area | Type | House Type | ...
        for table in soup.find_all("table"):
            headers_row = table.find("tr")
            if not headers_row:
                continue
            ths = [th.get_text(strip=True).lower() for th in headers_row.find_all(["th","td"])]
            if "year built" in ths and ("gross living area" in ths or "house type" in ths):
                for dr in table.find_all("tr")[1:]:
                    cells = [td.get_text(strip=True) for td in dr.find_all("td")]
                    if not cells:
                        continue
                    def _char(name):
                        try:
                            idx = next(i for i,h in enumerate(ths) if name in h)
                            return cells[idx] if idx < len(cells) else None
                        except StopIteration:
                            return None
                    ht = _char("house type")
                    if ht and not result["scout_house_type"]:
                        result["scout_house_type"] = ht
                break

        # Sq ft breakdown from "Residential Sq Ft Breakdown" table or text
        m = re.search(r'Basement\s+([\d,]+)', full_text, re.IGNORECASE)
        if m:
            result["scout_basement_sqft"] = int(m.group(1).replace(",", ""))

        # Garage sq ft
        m = re.search(r'(?:Detached Garage|Attached Garage|Garage)[^\d]*([\d]+)SF', full_text, re.IGNORECASE)
        if m:
            result["scout_garage_sqft"] = int(m.group(1))

        # ── Sales History ─────────────────────────────────────────────────────
        sales = []
        for table in soup.find_all("table"):
            headers_row = table.find("tr")
            if not headers_row:
                continue
            ths = [th.get_text(strip=True).lower() for th in headers_row.find_all(["th","td"])]
            if "sale date" in ths and "sale price" in ths:
                for dr in table.find_all("tr")[1:]:
                    cells = [td.get_text(strip=True) for td in dr.find_all("td")]
                    if not cells:
                        continue
                    try:
                        date_idx  = next(i for i,h in enumerate(ths) if "sale date" in h)
                        price_idx = next(i for i,h in enumerate(ths) if "sale price" in h)
                        inst_idx  = next(i for i,h in enumerate(ths) if "instrument" in h or "sale instrument" in h)
                        sale_date  = cells[date_idx]  if date_idx  < len(cells) else ""
                        sale_price = cells[price_idx] if price_idx < len(cells) else ""
                        instrument = cells[inst_idx]  if inst_idx  < len(cells) else ""
                        price_val  = _money(sale_price) if sale_price else None
                        if sale_date or price_val:
                            sales.append({"date": sale_date, "price": price_val, "instrument": instrument})
                    except (StopIteration, IndexError):
                        continue
                break
        if sales:
            result["scout_sales"] = _json.dumps(sales)
            # Populate top-level last_sale from most recent row
            result["last_sale_price"] = sales[0].get("price")
            result["last_sale_date"]  = sales[0].get("date")

        # ── Permits ───────────────────────────────────────────────────────────
        permits = []
        for table in soup.find_all("table"):
            headers_row = table.find("tr")
            if not headers_row:
                continue
            ths = [th.get_text(strip=True).lower() for th in headers_row.find_all(["th","td"])]
            if "permit number" in ths and "filing date" in ths:
                for dr in table.find_all("tr")[1:]:
                    cells = [td.get_text(strip=True) for td in dr.find_all("td")]
                    if not cells:
                        continue
                    try:
                        num_idx  = next(i for i,h in enumerate(ths) if "permit number" in h)
                        date_idx = next(i for i,h in enumerate(ths) if "filing date" in h or "date" in h)
                        desc_idx = next(i for i,h in enumerate(ths) if "description" in h)
                        permits.append({
                            "number":      cells[num_idx]  if num_idx  < len(cells) else "",
                            "date":        cells[date_idx] if date_idx < len(cells) else "",
                            "description": cells[desc_idx] if desc_idx < len(cells) else "",
                        })
                    except (StopIteration, IndexError):
                        continue
                break
        if permits:
            result["scout_permits"] = _json.dumps(permits)

        logger.info(f"SCOUT fetch OK for APN {apn}: owner={result['owner_name']}, "
                    f"value={result['assessed_value']}, sales={len(sales)}, permits={len(permits)}")
    except Exception as e:
        logger.warning(f"SCOUT fetch error for APN {apn}: {e}", exc_info=True)

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
            for field in [
                "owner_name", "owner_address",
                "assessed_value", "assessed_land", "assessed_building",
                "annual_taxes", "taxes_owing",
                "last_sale_price", "last_sale_date",
                "scout_legal", "scout_parcel_class", "scout_tca",
                "scout_land_sqft", "scout_house_type",
                "scout_basement_sqft", "scout_garage_sqft",
                "scout_sales", "scout_permits",
            ]:
                if scout.get(field) is not None:
                    setattr(prop, field, scout[field])
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
