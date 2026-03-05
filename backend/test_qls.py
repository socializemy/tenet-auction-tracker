import asyncio
from scrapers.quality_loan import QualityLoanScraper
import logging

logging.basicConfig(level=logging.INFO)

async def test():
    scraper = QualityLoanScraper()
    await scraper.scrape()

if __name__ == "__main__":
    asyncio.run(test())
