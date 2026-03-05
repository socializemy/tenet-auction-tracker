from typing import List, Dict, Any
from scrapers.base import BaseScraper
import logging
import re

logger = logging.getLogger(__name__)

class AuctionComScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            source_name="Auction.com",
            base_url="https://www.auction.com/residential/wa/spokane-county/"
        )

    async def _extract_data(self, page) -> List[Dict[str, Any]]:
        properties = []

        logger.info(f"Navigating to {self.base_url}")
        await page.goto(self.base_url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(3000)

        # Dismiss any cookie/consent overlays
        for selector in ['button:has-text("Accept")', 'button:has-text("OK")', '[id*="close"]']:
            try:
                el = page.locator(selector).first
                if await el.is_visible(timeout=2000):
                    await el.click()
                    await page.wait_for_timeout(500)
            except Exception:
                pass

            # Wait for content to load
            await page.wait_for_selector('[class*="base-card"], [data-elm-id^="property_card_asset"]', timeout=20000)
            
            # Scroll the virtualized list container to load all cards and parse as we go
            container_selector = '[class*="q__list--"]'
            container = await page.query_selector(container_selector)
            
            scraped_ids = set()
            
            if container:
                logger.info("Found virtualized list container, scrolling...")
                # Get total height of the inner container
                inner_height = await page.evaluate(f'''() => {{
                    const inner = document.querySelector('{container_selector} > div');
                    return inner ? parseInt(inner.style.height) : 0;
                }}''')
                
                # Scroll down in increments
                current_scroll = 0
                while current_scroll <= inner_height + 1000:
                    await page.evaluate(f'''(scroll) => {{
                        document.querySelector('{container_selector}').scrollTop = scroll;
                    }}''', current_scroll)
                    await page.wait_for_timeout(500) # Give it time to render and fetch
                    
                    # Parse current visible cards
                    cards = await page.query_selector_all(
                        '[class*="asset-root"], [data-elm-id$="_root"]'
                    )
                    
                    for card in cards:
                        try:
                            # Use test-id or link to get a unique identifier
                            link_el = await card.query_selector('a')
                            if not link_el:
                                continue
                            
                            href = await link_el.get_attribute('href')
                            if not href:
                                continue
                                
                            if href in scraped_ids:
                                continue
                            
                            scraped_ids.add(href)
                            source_url = href if href.startswith('http') else f"https://www.auction.com{href}"
                            
                            card_text = (await card.inner_text()) or ""

                            # Extract address
                            address_el = await card.query_selector(
                                '[data-testid="address"], .address, h2, h3, [class*="address"]'
                            )
                            address = (await address_el.inner_text()).strip() if address_el else ""

                            if not address:
                                continue

                            # Extract city
                            city = "Spokane"
                            if "Spokane Valley" in card_text:
                                city = "Spokane Valley"

                            # Extract price
                            price_el = await card.query_selector(
                                '[class*="property-value-amount"], [class*="amount"], [class*="value-amount"]'
                            )
                            price_text = (await price_el.inner_text()).strip() if price_el else "0"
                            price_num = re.sub(r'[^\d.]', '', price_text)
                            starting_bid = float(price_num) if price_num else 0.0

                            # Extract auction date / time status
                            auction_date = ""
                            # Look for patterns like "Starts in 2 days" or "Oct 24" / "Oct 24 - 26"
                            starts_in_match = re.search(r'Starts in \d+ days?', card_text, re.IGNORECASE)
                            date_match = re.search(r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}(?: - (?:\w+ )?\d{1,2})?', card_text, re.IGNORECASE)
                            
                            if date_match:
                                auction_date = date_match.group(0)
                            elif starts_in_match:
                                auction_date = starts_in_match.group(0)
                                
                            if not auction_date:
                                date_el = await card.query_selector('[data-elm-id="info-pill"]:has-text("Ends in"), [class*="date"], [class*="auction"]')
                                auction_date = (await date_el.inner_text()).strip() if date_el else ""

                            # Extract image
                            img_el = await card.query_selector('span[role="img"], img')
                            image_url = ""
                            if img_el:
                                style = await img_el.get_attribute('style')
                                if style and 'background-image: url(' in style:
                                    match = re.search(r'url\("([^"]+)"\)', style)
                                    if match:
                                        image_url = match.group(1).replace("&amp;", "&")
                                else:
                                    image_url = await img_el.get_attribute('src') or ""

                            properties.append({
                                "source": self.source_name,
                                "tsn": "",
                                "address": address,
                                "city": city,
                                "county": "Spokane",
                                "zip_code": "",
                                "auction_date": auction_date,
                                "auction_time": "",
                                "starting_bid": starting_bid,
                                "status": "Active",
                                "source_url": source_url,
                                "image_url": image_url,
                            })
                        except Exception as e:
                            logger.error(f"Error parsing property component: {str(e)}")
                            
                    # Move to next chunk
                    current_scroll += 800
                
                # Check for next page of the container
                next_button = await page.query_selector('[aria-label="Next"], .next, [class*="pagination-next"]')
                if next_button and not await next_button.is_disabled():
                    await next_button.click()
                    await page.wait_for_timeout(2000)
                    page_num += 1
                else:
                    break # No more pages or virtualized list exhausted
            else:
                # If no virtualized list container, try scraping all visible cards once
                logger.info(f"No virtualized list container found on page {page_num}, scraping visible cards.")
                cards = await page.query_selector_all(
                    '[class*="asset-root"], [data-elm-id$="_root"]'
                )
                if not cards:
                    # Fallback: try scraping structured data from page if no cards found at all
                    logger.warning("No card elements found — trying JSON-LD structured data")
                    json_ld = await page.evaluate('''() => {
                        const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                        return Array.from(scripts).map(s => s.textContent);
                    }''')
                    for raw in json_ld:
                        try:
                            import json
                            data = json.loads(raw)
                            if isinstance(data, dict) and '@graph' in data:
                                items_to_check = data['@graph']
                            elif isinstance(data, list):
                                items_to_check = data
                            else:
                                items_to_check = [data]
                                
                            for item in items_to_check:
                                if item.get('@type') in ('RealEstateListing', 'Product', 'Offer', 'SingleFamilyResidence'):
                                    name = item.get('name', '')
                                    url = item.get('url', '')
                                    price = item.get('price') or item.get('offers', {}).get('price', 0)
                                    addr = item.get('address', {})
                                    street = addr.get('streetAddress', name)
                                    city = addr.get('addressLocality', 'Spokane')
                                    if 'Spokane' in city or 'Spokane' in street:
                                        properties.append({
                                            "source": self.source_name,
                                            "tsn": "",
                                            "address": street,
                                            "city": city,
                                            "county": "Spokane",
                                            "zip_code": addr.get('postalCode', ''),
                                            "auction_date": "",
                                            "auction_time": "",
                                            "starting_bid": float(price) if price else 0.0,
                                            "status": "Active",
                                            "source_url": url,
                                            "image_url": item.get('image', ''),
                                        })
                        except Exception:
                            pass
                else:
                    # Process cards found if no virtualized list
                    for card in cards:
                        try:
                            link_el = await card.query_selector('a')
                            if not link_el:
                                continue
                            
                            href = await link_el.get_attribute('href')
                            if href in scraped_ids:
                                continue
                            
                            scraped_ids.add(href)
                            source_url = href if href.startswith('http') else f"https://www.auction.com{href}"
                            
                            card_text = await card.inner_text()

                            address_el = await card.query_selector(
                                '[data-testid="address"], .address, h2, h3, [class*="address"]'
                            )
                            address = (await address_el.inner_text()).strip() if address_el else ""

                            if not address or 'Spokane' not in card_text:
                                continue

                            city = "Spokane"
                            if "Spokane Valley" in card_text:
                                city = "Spokane Valley"

                            price_el = await card.query_selector(
                                '[class*="property-value-amount"], [class*="amount"], [class*="value-amount"]'
                            )
                            price_text = (await price_el.inner_text()).strip() if price_el else "0"
                            price_num = re.sub(r'[^\d.]', '', price_text)
                            starting_bid = float(price_num) if price_num else 0.0

                            date_el = await card.query_selector('[data-elm-id="info-pill"]:has-text("Ends in"), [class*="date"], [class*="auction"]')
                            auction_date = (await date_el.inner_text()).strip() if date_el else ""

                            img_el = await card.query_selector('span[role="img"], img')
                            image_url = ""
                            if img_el:
                                style = await img_el.get_attribute('style')
                                if style and 'background-image: url(' in style:
                                    match = re.search(r'url\("([^"]+)"\)', style)
                                    if match:
                                        image_url = match.group(1).replace("&amp;", "&")
                                else:
                                    image_url = await img_el.get_attribute('src') or ""

                            properties.append({
                                "source": self.source_name,
                                "tsn": "",
                                "address": address,
                                "city": city,
                                "county": "Spokane",
                                "zip_code": "",
                                "auction_date": auction_date,
                                "auction_time": "",
                                "starting_bid": starting_bid,
                                "status": "Active",
                                "source_url": source_url,
                                "image_url": image_url,
                            })
                        except Exception as card_err:
                            logger.warning(f"Card parse error: {card_err}")
                            continue

                # Pagination for non-virtualized lists
                try:
                    next_btn = page.locator('[aria-label="Next page"], button:has-text("Next"), a:has-text("Next")')
                    if await next_btn.count() > 0 and await next_btn.first.is_enabled():
                        await next_btn.first.click()
                        await page.wait_for_load_state("networkidle", timeout=15000)
                        page_num += 1
                    else:
                        break # No more pages
                except Exception:
                    break # Error during pagination, stop

        logger.info(f"Auction.com: scraped {len(properties)} Spokane properties")
        return properties
