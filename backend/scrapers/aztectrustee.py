from typing import List, Dict, Any
from scrapers.base import BaseScraper
import logging
import re

logger = logging.getLogger(__name__)

class AztecTrusteeScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            source_name="Aztec Trustee WA",
            base_url="https://www.aztectrustee-wa.com/"
        )

    async def _extract_data(self, page) -> List[Dict[str, Any]]:
        properties = []

        logger.info(f"Navigating to {self.base_url}")
        await page.goto(self.base_url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)

        # Try clicking a Spokane county link/tab if available
        try:
            spokane_link = page.locator('a:has-text("Spokane"), td:has-text("Spokane")')
            if await spokane_link.count() > 0:
                await spokane_link.first.click()
                await page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass

        rows = await page.query_selector_all('table tr, .notice-item, .property-row')
        logger.info(f"Aztec Trustee: found {len(rows)} rows")

        for row in rows:
            try:
                row_text = await row.inner_text()
                if "Spokane" not in row_text:
                    continue

                cells = await row.query_selector_all('td')
                if len(cells) < 2:
                    continue

                texts = [(await c.inner_text()).strip() for c in cells]

                tsn = ""
                address = ""
                sale_date = ""

                for t in texts:
                    if re.match(r'\d{2}/\d{2}/\d{4}', t) and not sale_date:
                        sale_date = t
                    elif re.match(r'\d+\s+\w+', t) and not address:
                        address = t
                    elif re.match(r'WA-\d+|\d{4}-\d+', t) and not tsn:
                        tsn = t

                if not address:
                    address = next((
                        t for t in texts
                        if re.search(r'\d+\s+\w+\s+(st|ave|rd|dr|blvd|way|ln|ct|pl)', t, re.I)
                    ), "")

                city = "Spokane Valley" if "Spokane Valley" in row_text else "Spokane"

                link = await row.query_selector('a')
                source_url = ""
                if link:
                    href = await link.get_attribute('href')
                    if href:
                        source_url = href if href.startswith('http') else f"https://www.aztectrustee-wa.com/{href.lstrip('/')}"

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
                        "status": "Active",
                        "source_url": source_url,
                    })
            except Exception as e:
                logger.warning(f"Aztec Trustee row error: {e}")

        logger.info(f"Aztec Trustee WA: scraped {len(properties)} Spokane properties")
        return properties
