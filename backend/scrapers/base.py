import os
import asyncio
from typing import List, Dict, Any
from playwright.async_api import async_playwright
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseScraper:
    def __init__(self, source_name: str, base_url: str, headless: bool = True):
        self.source_name = source_name
        self.base_url = base_url
        self.headless = headless

    async def scrape(self) -> List[Dict[str, Any]]:
        """
        Main method to trigger scraping.
        Must return a list of dictionaries where each dictionary 
        represents a property.
        """
        logger.info(f"Starting scrape for {self.source_name}")
        print("DEBUG: entering async_playwright context")
        async with async_playwright() as p:
            print(f"DEBUG: launching chromium with headless={self.headless}")
            
            # Use CHROME_BIN_PATH for Docker/Linux overriding, default to macOS Chrome
            chrome_path = os.environ.get(
                'CHROME_BIN_PATH', 
                '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
            )
            
            # Stealth approach: Use native Chrome binary AND force Headed
            browser = await p.chromium.launch(
                headless=False,
                executable_path=chrome_path
            )
            print("DEBUG: creating new page directly from browser")
            page = await browser.new_page()
            print("DEBUG: executing _extract_data")
            
            try:
                properties = await self._extract_data(page)
                logger.info(f"Successfully scraped {len(properties)} properties from {self.source_name}")
                return properties
            except Exception as e:
                logger.error(f"Error scraping {self.source_name}: {str(e)}")
                return []
            finally:
                await browser.close()

    async def _extract_data(self, page) -> List[Dict[str, Any]]:
        """
        To be implemented by child classes.
        Extracts property data from the page.
        """
        raise NotImplementedError
