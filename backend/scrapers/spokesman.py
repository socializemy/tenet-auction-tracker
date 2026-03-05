from typing import List, Dict, Any
from scrapers.base import BaseScraper
import logging
import re

logger = logging.getLogger(__name__)

class SpokesmanDiscoveryScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            source_name="Spokesman-Review",
            base_url="https://spokesman.column.us/search?q=Trustee+Sale"
        )
        # Using a more robust query based on the Washington law for non-judicial foreclosure
        self.search_url = "https://spokesman.column.us/search?q=Notice+of+Trustee%27s+Sale"

    async def _extract_data(self, page) -> List[Dict[str, Any]]:
        discovered_sales = []
        
        logger.info(f"Navigating to base url: https://spokesman.column.us/search")
        await page.goto("https://spokesman.column.us/search", wait_until="domcontentloaded")
        
        try:
            logger.info("Waiting for search input...")
            # Column uses standard inputs for search, usually placeholder="Search" or similar
            search_input = page.locator('input[placeholder*="Search"], input[type="search"], input[name="q"]').first
            await search_input.wait_for(timeout=10000)
            
            logger.info("Entering search query...")
            await search_input.fill("Trustee Sale")
            await search_input.press("Enter")
        except Exception as e:
            logger.error(f"Failed to perform interactive search: {e}")
        
        # Wait for the results to load
        try:
            logger.info("Waiting for legal notice results to load...")
            await page.wait_for_timeout(5000) # Give the SPA time to render the cards after search
            await page.wait_for_selector('div.public-notice-result', state='attached', timeout=15000)
            logger.info("Results loaded.")
        except Exception as e:
            logger.warning(f"Timeout waiting for results or no results found: {e}")
            content = await page.content()
            with open("spokesman_column_debug.html", "w") as f:
                f.write(content)
            return discovered_sales

        # Wait a moment for any dynamic rendering
        await page.wait_for_timeout(3000)

        # Scrape the public notice cards
        notice_cards = await page.query_selector_all('div.public-notice-result')
        logger.info(f"Found {len(notice_cards)} notice cards on the first page.")

        for card in notice_cards:
            try:
                # The text is usually inside a container within the card. We can grab the full inner text.
                card_text = await card.inner_text()
                logger.info(f"--- CARD TEXT PREVIEW ---\n{card_text[:300]}...\n-------------------------")
                
                # Basic parsing logic for Trustee Sale Number
                # Usually looks like "TS No: 12345-WA", "Trustee Sale No. WA-12345", etc.
                tsn_match = re.search(r'(?:TS\s*No\.?|Trustee\s*Sale\s*No\.?|T\.S\.\s*No\.?)[\s:]*([A-Za-z0-9-]+)', card_text, re.IGNORECASE)
                tsn = tsn_match.group(1).strip() if tsn_match else None
                
                # Attempt to extract an address (this is very heuristic and might need refinement)
                # Look for common road suffixes near city/state
                address_match = re.search(r'([0-9]+\s+(?:[NnSsEeWw]\.?\s+)?[A-Za-z0-9\s]+(?:Ave|St|Rd|Blvd|Ln|Dr|Way|Ct|Pl|Terr?|Hwy).*?SPOKANE[\s,]*(?:WA|Washington)?)', card_text, re.IGNORECASE | re.DOTALL)
                address = address_match.group(1).strip().replace('\n', ' ') if address_match else None
                
                if tsn:
                    discovered_sales.append({
                        "source": self.source_name,
                        "tsn": tsn,
                        "address": address or "Address parsing complex, see raw text",
                        "raw_text_snippet": card_text[:200] + "..." # Save a snippet for context
                    })
            except Exception as e:
                logger.error(f"Error parsing individual notice card: {e}")

        logger.info(f"Extracted {len(discovered_sales)} TSNs from the page.")
        return discovered_sales
