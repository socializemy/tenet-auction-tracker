import asyncio
import logging

from scrapers.insourcelogic import InsourceLogicScraper

logging.basicConfig(level=logging.INFO)

async def test_scraper():
    print("Testing Insource Logic offline scraper...")
    scraper = InsourceLogicScraper()
    results = await scraper.scrape()
    
    print("\nScrape completed, returned", type(results), "with length", len(results))
    print(f"\nScraped {len(results)} properties.\n")
    
    for i, prop in enumerate(results, 1):
        print(f"[{i}] {prop['address']} | {prop['city']} | TSN: {prop['tsn']} | Bids: ${prop.get('starting_bid')} | APN: {prop.get('apn')} | Date: {prop.get('auction_date')}")

if __name__ == "__main__":
    asyncio.run(test_scraper())
