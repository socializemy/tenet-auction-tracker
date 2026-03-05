from typing import List, Dict, Any
from scrapers.base import BaseScraper
import logging
import re

logger = logging.getLogger(__name__)

class ElitePostScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            source_name="Elite Post & Pub",
            base_url="https://elitepostandpub.com/index.php"
        )

    async def _extract_data(self, page) -> List[Dict[str, Any]]:
        properties = []

        logger.info(f"Navigating to {self.base_url}")
        await page.goto(self.base_url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)

        # Try to click/filter for Washington or Spokane if options are present
        try:
            state_select = page.locator('select[name*="state"], select[name*="State"]')
            if await state_select.count() > 0:
                await state_select.select_option(value="WA", timeout=3000)
                await page.wait_for_timeout(1500)
        except Exception:
            pass

        rows = await page.query_selector_all('table tr, .notice-row, .listing-row')
        logger.info(f"Elite Post: found {len(rows)} rows")

        for row in rows:
            try:
                row_text = await row.inner_text()
                if "Spokane" not in row_text and "spokane" not in row_text.lower():
                    continue

                cells = await row.query_selector_all('td')
                if len(cells) < 2:
                    continue

                texts = [(await c.inner_text()).strip() for c in cells]

                tsn = ""
                address = ""
                sale_date = ""
                status = "Active"

                for t in texts:
                    if re.match(r'\d{2}/\d{2}/\d{4}', t) and not sale_date:
                        sale_date = t
                    elif re.match(r'\d+\s+\w+', t) and not address:
                        address = t
                    elif re.match(r'WA-\d+|\d{4}-\d+', t) and not tsn:
                        tsn = t

                if not address and texts:
                    address = next((t for t in texts if re.search(r'\d+\s+\w+\s+(st|ave|rd|dr|blvd|way|ln|ct|pl)', t, re.I)), texts[0] if texts else "")

                city = "Spokane Valley" if "Spokane Valley" in row_text else "Spokane"

                link = await row.query_selector('a')
                source_url = ""
                if link:
                    href = await link.get_attribute('href')
                    if href:
                        source_url = href if href.startswith('http') else f"https://elitepostandpub.com/{href.lstrip('/')}"

                if address:
                    properties.append({
                        "source": self.source_name,
                        "tsn": tsn,
                        "address": address,
                        "city": city,
                        "county": "Spokane",
                        "zip_code": "",
                        "auction_date": sale_date,
                        "auction_time": "10:00 AM",
                        "starting_bid": 0.0,
                        "status": status,
                        "source_url": source_url,
                    })
            except Exception as e:
                logger.warning(f"Elite Post row error: {e}")

        logger.info(f"Elite Post & Pub: scraped {len(properties)} Spokane properties")
        return properties
