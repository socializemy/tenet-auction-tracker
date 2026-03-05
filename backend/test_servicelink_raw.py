import asyncio
import logging
from scrapers.servicelinkasap import ServiceLinkScraper

logging.basicConfig(level=logging.INFO)

async def test_scraper():
    scraper = ServiceLinkScraper()
    print(f"Testing {scraper.source_name} scraper...")
    
    # We test scrape without writing to DB first to verify output
    results = await scraper.scrape()
    
    print(f"\nScrape completed, returned {type(results)} with length {len(results)}")
    print(f"\nScraped {len(results)} properties.\n")
    
    for i, p in enumerate(results[:5]):
        print(f"[{i+1}] {p.get('address')} | {p.get('city')} | TSN: {p.get('tsn')} | Bids: ${p.get('starting_bid')} | APN: {p.get('apn')} | Date: {p.get('auction_date')}")

if __name__ == "__main__":
    asyncio.run(test_scraper())
