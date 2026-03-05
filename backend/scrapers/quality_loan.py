from typing import List, Dict, Any
from scrapers.base import BaseScraper
import logging
import os
import re

logger = logging.getLogger(__name__)

class QualityLoanScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            source_name="Quality Loan",
            base_url="https://www.qualityloan.com/QLSPortal/PagesPublic/Login.aspx"
        )
        self.username = os.environ.get("QUALITY_LOAN_USER", "CoJames1")
        self.password = os.environ.get("QUALITY_LOAN_PASS", "HJK4*#&90")

    async def _extract_data(self, page) -> List[Dict[str, Any]]:
        properties = []

        logger.info("Navigating to Quality Loan login page")
        await page.goto(self.base_url, wait_until="networkidle", timeout=30000)

        # --- Login ---
        try:
            # Use specific ID matching to avoid generic element overlap
            await page.fill('input[id$="UserName"]', self.username)
            await page.fill('input[id$="Password"]', self.password)

            # Quality Loan's new portal often hangs on expect_navigation for the login button
            login_btn = page.locator('text="Login"').last
            if await login_btn.count() > 0:
                await login_btn.click(timeout=10000)
            else:
                await page.press('input[id$="Password"]', 'Enter', no_wait_after=True)
                
            # Wait for network idle instead of expect_navigation due to ASP.NET redirects
            await page.wait_for_load_state("networkidle", timeout=15000)

            logger.info("Login successful (networkidle reached)")
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return properties

        # Accept any post-login terms modal
        try:
            for selector in ['input[value="I Accept"]', 'input[value="Accept"]', 'button:has-text("Accept")']:
                el = page.locator(selector)
                if await el.count() > 0:
                    await el.first.click()
                    await page.wait_for_timeout(2000)
                    break
        except Exception:
            pass

        # Verify we are on FileSearch (we might already be there post-login)
        if "FileSearch.aspx" not in page.url:
            logger.info("Navigating to File Search page explicitly")
            await page.goto(
                "https://www.qualityloan.com/QLSPortal/PagesAuthorized/FileSearch.aspx",
                wait_until="networkidle",
                timeout=20000
            )

        # Accept Terms of Use popup on search page if it appears again
        try:
            accept_popup = page.locator('input#btnAccept, input[value="I Accept"], input[value="Accept"]')
            if await accept_popup.is_visible(timeout=4000):
                await accept_popup.first.click()
                await page.wait_for_timeout(2000)
        except Exception:
            pass

        # --- Strategy: Bypass JS validation and search broadly for "Spokane" ---
        try:
            logger.info("Bypassing JS Validation for broad search.")
            await page.evaluate("if(typeof Page_ValidationActive !== 'undefined') Page_ValidationActive = false;")
            await page.evaluate("if(typeof ValidatorEnable !== 'undefined') { for(var i=0; i<Page_Validators.length; i++) ValidatorEnable(Page_Validators[i], false); }")
            
            address_input = page.locator('input[id$="txtStreetAddress"]')
            if await address_input.count() > 0:
                await address_input.first.fill("Spokane")
                
                # Submit the search
                submit_btn = page.locator('input[id$="cmdSubmitFileSearch"], input[value="Search"]')
                if await submit_btn.count() > 0:
                     await submit_btn.first.click(no_wait_after=True)
                else:
                     await address_input.first.press('Enter', no_wait_after=True)
            else:
                logger.warning("Could not find address line input to perform search.")
                
        except Exception as e:
            logger.warning(f"Search setup issue: {e}")

        await page.wait_for_timeout(5000)

        # --- parse results ---
        page_num = 1
        while True:
            logger.info(f"Parsing Quality Loan results page {page_num}...")

            # Try tables with property rows
            rows = await page.query_selector_all('table.gvFileSearch tr, table#gvFileSearch tr, table tr')
            data_rows = [r for r in rows if len(await r.query_selector_all('td')) >= 4]

            if not data_rows:
                logger.warning("No data rows found in Quality Loan results")
                break

            for row in data_rows:
                cells = await row.query_selector_all('td')
                try:
                    texts = [((await c.inner_text())).strip() for c in cells]

                    # Detect Spokane entries — county may be in various positions
                    row_text = " ".join(texts).upper()
                    if "SPOKANE" not in row_text:
                        continue

                    # Flexible column mapping based on content
                    tsn = ""
                    address = ""
                    sale_date = ""
                    sale_time = ""
                    status = ""

                    for i, t in enumerate(texts):
                        if re.match(r'\d{2}/\d{2}/\d{4}', t) and not sale_date:
                            sale_date = t
                        elif re.match(r'\d{1,2}:\d{2}', t) and not sale_time:
                            sale_time = t
                        elif re.match(r'\d+\s+\w+', t) and not address:
                            address = t
                        elif re.match(r'WA-\d+', t) and not tsn:
                            tsn = t

                    if not address and len(texts) > 1:
                        address = texts[1]

                    # Try to get link URL (detail page)
                    link_el = await cells[0].query_selector('a')
                    source_url = ""
                    if link_el:
                        href = await link_el.get_attribute('href')
                        if href:
                            source_url = href if href.startswith('http') else f"https://www.qualityloan.com{href}"

                    properties.append({
                        "source": self.source_name,
                        "tsn": tsn,
                        "address": address,
                        "city": "Spokane",
                        "county": "Spokane",
                        "zip_code": "",
                        "auction_date": sale_date,
                        "auction_time": sale_time,
                        "starting_bid": 0.0,
                        "status": status or "Active",
                        "source_url": source_url,
                    })
                except Exception as row_err:
                    logger.warning(f"Row parse error: {row_err}")
                    continue

            # Try to paginate
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

        logger.info(f"Quality Loan: scraped {len(properties)} Spokane properties")
        return properties
