from typing import List, Dict, Any
from scrapers.base import BaseScraper
import logging
import re

logger = logging.getLogger(__name__)

class NationwideScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            source_name="Nationwide Posting",
            base_url="https://search.nationwideposting.com/SearchTerms.aspx"
        )

    async def _extract_data(self, page) -> List[Dict[str, Any]]:
        properties = []

        logger.info(f"Navigating to {self.base_url}")
        await page.goto(self.base_url, wait_until="networkidle", timeout=30000)

        # Accept terms if prompted
        try:
            accept_btn = page.locator('input[name="ctl00$contentMain$btnAccept"]')
            if await accept_btn.is_visible(timeout=5000):
                await accept_btn.click()
                logger.info("Accepted Terms of Use")
                await page.wait_for_timeout(2000)
        except Exception:
            logger.info("No terms accept button found — already accepted or not shown")

        # Select Washington state
        try:
            await page.select_option(
                'select[name="ctl00$contentLeftColumn$ddlState"]',
                value="WA",
                timeout=10000
            )
            logger.info("Selected state: WA")
            await page.wait_for_timeout(3000)  # Wait for AJAX county reload

            # Try to select Spokane county if the dropdown loads
            try:
                county_select = page.locator('select[name="ctl00$contentLeftColumn$ddlCounty"]')
                if await county_select.is_visible(timeout=3000):
                    await county_select.select_option(label="Spokane", timeout=5000)
                    logger.info("Selected county: Spokane")
                    await page.wait_for_timeout(1000)
            except Exception:
                logger.info("County dropdown not found or failed — will filter after search")

            # Click search button
            await page.click('input[name="ctl00$contentLeftColumn$imgBtnSearch"]', timeout=5000)
            logger.info("Clicked search button")
            await page.wait_for_load_state("networkidle", timeout=20000)

        except Exception as e:
            logger.error(f"Error setting search filters: {e}")
            return properties

        # Handle pagination
        page_num = 1
        while True:
            logger.info(f"Parsing results page {page_num}...")
            rows = await page.query_selector_all('table#ctl00_contentMain_gvSearchResult tr')

            if not rows:
                logger.warning("No result rows found")
                break

            for row in rows[1:]:  # Skip header row
                cells = await row.query_selector_all('td')
                if len(cells) < 7:
                    continue

                # Filter to Spokane county only
                county_text = (await cells[3].inner_text()).strip().upper()
                if "SPOKANE" not in county_text:
                    continue

                try:
                    tsn_cell = await cells[0].inner_text()
                    tsn = tsn_cell.strip()

                    date_str = (await cells[1].inner_text()).strip()
                    time_str = (await cells[2].inner_text()).strip()

                    address_td = await cells[5].inner_text()
                    address_parts = [p.strip() for p in address_td.split('\n') if p.strip()]
                    address = address_parts[0] if address_parts else ""
                    city_raw = address_parts[1] if len(address_parts) > 1 else ""
                    city = city_raw.split(',')[0].strip().title() if ',' in city_raw else city_raw.title()

                    status = (await cells[6].inner_text()).strip().replace('\n', ' ')

                    # Try to grab source URL from link in TSN cell
                    link_el = await cells[0].query_selector('a')
                    source_url = ""
                    if link_el:
                        href = await link_el.get_attribute('href')
                        if href:
                            source_url = href if href.startswith('http') else f"https://search.nationwideposting.com/{href.lstrip('/')}"

                    properties.append({
                        "source": self.source_name,
                        "tsn": tsn,
                        "address": address,
                        "city": city,
                        "county": "Spokane",
                        "zip_code": "",
                        "auction_date": date_str,
                        "auction_time": time_str,
                        "starting_bid": 0.0,
                        "status": status,
                        "source_url": source_url,
                    })
                except Exception as row_err:
                    logger.warning(f"Error parsing row: {row_err}")
                    continue

            logger.info(f"Found {len(properties)} Spokane properties so far on page {page_num}")

            # Try to go to next page
            try:
                next_btn = page.locator('a:has-text("Next"), input[value="Next >"]')
                if await next_btn.count() > 0 and await next_btn.first.is_enabled():
                    await next_btn.first.click()
                    await page.wait_for_load_state("networkidle", timeout=15000)
                    page_num += 1
                else:
                    break
            except Exception:
                break

        logger.info(f"Nationwide: scraped {len(properties)} Spokane properties total")
        return properties
