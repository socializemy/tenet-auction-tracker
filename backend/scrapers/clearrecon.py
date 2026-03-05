from typing import List, Dict, Any
from scrapers.base import BaseScraper
import logging

logger = logging.getLogger(__name__)

class ClearReconScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            source_name="Clear Recon WA",
            base_url="https://clearrecon-wa.com/washington-listings/"
        )

    async def _extract_data(self, page) -> List[Dict[str, Any]]:
        properties = []

        logger.info(f"Navigating to {self.base_url}")
        await page.goto(self.base_url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)

        # Handle disclaimer
        try:
            agree_btn = page.locator('a:has-text("Agree")')
            if await agree_btn.count() > 0:
                logger.info("Found Agree button, clicking...")
                await agree_btn.first.click()
                await page.wait_for_load_state("networkidle")
                await page.wait_for_timeout(3000)
        except Exception as e:
            logger.info(f"Agree button not found or error clicking: {e}")

        # Try to select "All" from the DataTables dropdown
        try:
            logger.info("Setting entries per page to All...")
            await page.evaluate('''() => {
                const select = document.querySelector('select[name$="_length"]');
                if (select) {
                    select.value = '-1';
                    select.dispatchEvent(new Event('change'));
                }
            }''')
            # Wait for datatable to reload
            await page.wait_for_timeout(3000)
        except Exception as e:
            logger.warning(f"Could not change entries to All: {e}")

        logger.info("Parsing property rows...")
        rows = await page.query_selector_all('table.posts-data-table > tbody > tr')
        
        if not rows:
            logger.warning("No result rows found on Clear Recon WA")
            return properties

        logger.info(f"Found {len(rows)} rows on Clear Recon WA page")

        for row in rows:
            try:
                # Check for "Spokane" before digging into columns
                row_text = await row.inner_text()
                if "Spokane" not in row_text and "SPOKANE" not in row_text.upper():
                    continue

                cells = await row.query_selector_all('td')
                if len(cells) < 5:
                    continue

                # DataTables puts the TS Number in column 0, Address in 1, Date in 2, Time in 3, Location in 4
                tsn = (await cells[0].inner_text()).strip()
                address_full = (await cells[1].inner_text()).strip()
                sale_date = (await cells[2].inner_text()).strip()
                sale_time = (await cells[3].inner_text()).strip()
                
                # Try to extract a clean address and city from the combined address string
                # E.g. "8525 N Weipert Dr, Spokane WA, 99208"
                parts = address_full.split(',')
                address = parts[0].strip() if len(parts) > 0 else address_full
                
                city = "Spokane"
                if len(parts) > 1:
                    city_part = parts[1].strip()
                    if city_part.upper().endswith("WA"):
                         city = city_part[:-2].strip()
                    else:
                         city = city_part
                
                # Check city again just to be safe, or if it says Spokane Valley
                if "SPOKANE" in address_full.upper():
                    if "SPOKANE VALLEY" in address_full.upper():
                        city = "Spokane Valley"
                    else:
                        city = "Spokane"

                # Look for a detail link (maybe in TS Number cell)
                source_url = self.base_url
                link = await cells[0].query_selector('a')
                if link:
                    href = await link.get_attribute('href')
                    if href:
                        source_url = href if href.startswith('http') else f"https://clearrecon-wa.com{href}"

                if tsn and address:
                    properties.append({
                        "source": self.source_name,
                        "tsn": tsn,
                        "address": address,
                        "city": city,
                        "county": "Spokane",
                        "zip_code": "",
                        "auction_date": sale_date,
                        "auction_time": sale_time,
                        "starting_bid": 0.0,
                        "status": "Active",
                        "source_url": source_url,
                    })
            except Exception as e:
                logger.warning(f"Clear Recon row error: {e}")
                continue

        logger.info(f"Clear Recon WA: scraped {len(properties)} Spokane properties")
        return properties
