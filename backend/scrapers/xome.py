from typing import List, Dict, Any
from scrapers.base import BaseScraper
import logging
import re

logger = logging.getLogger(__name__)

class XomeScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            source_name="Xome",
            base_url="https://www.xome.com/auctions/listing/WA/Spokane",
            headless=True
        )

    async def _extract_data(self, page) -> List[Dict[str, Any]]:
        properties = []

        logger.info(f"Navigating to {self.base_url}")
        
        # Load the page and wait for the React components to mount
        await page.goto(self.base_url, wait_until="domcontentloaded", timeout=60000)
        logger.info("Page loaded. Waiting 8s for React to mount cards...")
        await page.wait_for_timeout(8000)

        logger.info("Parsing Xome cards...")
        
        cards = await page.query_selector_all('div.srp-property-card')

        if not cards:
            logger.warning("No Xome listing cards found on this page")
            return properties

        for card in cards:
            try:
                card_text = await card.inner_text()

                # Address Extraction
                addr_el = await card.query_selector('[class*="address"], h2, h3')
                address_raw = (await addr_el.inner_text()).strip() if addr_el else ""
                
                # Split city/state from street address if bundled
                address_lines = [line.strip() for line in address_raw.split('\n') if line.strip()]
                address = address_lines[0] if address_lines else ""
                
                city = "Spokane"
                if "Spokane Valley" in card_text or (len(address_lines) > 1 and "Spokane Valley" in address_lines[1]):
                    city = "Spokane Valley"

                # Starting Bid Extraction
                price_el = await card.query_selector('[class*="price"], [class*="Price"], [class*="bid"]')
                price_text = (await price_el.inner_text()).strip() if price_el else "0"
                price_num = re.sub(r'[^\d.]', '', price_text)
                try:
                    starting_bid = float(price_num) if price_num and price_num != "." else 0.0
                except ValueError:
                    starting_bid = 0.0

                # Auction Date Extraction
                date_el = await card.query_selector('[class*="date"], [class*="Date"]')
                auction_date = (await date_el.inner_text()).strip() if date_el else ""

                # Image URL
                img_el = await card.query_selector('img')
                image_url = (await img_el.get_attribute('src') or "") if img_el else ""

                # Property Link
                # Sometimes the card itself is an anchor tag, sometimes it contains one.
                href = await card.get_attribute('href')
                if not href:
                    link_el = await card.query_selector('a.property-link, a')
                    href = await link_el.get_attribute('href') if link_el else ""
                    
                source_url = ""
                if href:
                    source_url = href if href.startswith('http') else f"https://www.xome.com{href}"

                if address:
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
                logger.warning(f"Xome card extraction error: {e}")

        logger.info(f"Xome: scraped {len(properties)} properties")
        return properties
