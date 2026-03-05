import asyncio
from scrapers.spokesman import SpokesmanDiscoveryScraper
import logging
import json

logging.basicConfig(level=logging.INFO)

async def test():
    scraper = SpokesmanDiscoveryScraper()
    results = await scraper.scrape()
    print(json.dumps(results[:5], indent=2))

if __name__ == "__main__":
    asyncio.run(test())
