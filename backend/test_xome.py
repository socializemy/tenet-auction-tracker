import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.xome import XomeScraper
import logging

logging.basicConfig(level=logging.INFO)

async def test():
    try:
        print("Initializing Xome Scraper...")
        scraper = XomeScraper()
        print("Scraper instance created.")
        print("Running scrape (this will launch Playwright)...")
        results = await scraper.scrape()
        print(f"Scrape completed, returned {type(results)} with length {len(results)}")
        
        print(f"\nScraped {len(results)} properties from Xome.\n")
        for i, res in enumerate(results[:5]):
             print(f"[{i+1}] {res['address']} | {res['city']} | Starting Bid: {res['starting_bid']} | Date: {res['auction_date']}")
    except Exception as e:
        print(f"FATAL INNER EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(test())
    except Exception as e:
        print(f"FATAL OUTER EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
