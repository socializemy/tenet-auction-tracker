import asyncio
import sys
import logging
from backend.scrapers.auction_com import AuctionComScraper

logging.basicConfig(level=logging.INFO)

async def test_scraper():
    print("Testing Auction.com Scraper class...")
    scraper = AuctionComScraper()
    results = await scraper.scrape()
    print(f"Found {len(results)} properties!")
    for i, p in enumerate(results[:5]):
        print(f"{i+1}. {p.get('address')} - {p.get('starting_bid')}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_scraper())
