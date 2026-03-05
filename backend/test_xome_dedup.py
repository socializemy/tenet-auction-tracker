import asyncio
import logging
from database import SessionLocal, init_db
from deduplication import upsert_properties
from scrapers.xome import XomeScraper

logging.basicConfig(level=logging.INFO)

async def run_xome_only():
    init_db()
    scraper = XomeScraper()
    print("Running Xome scraper...")
    results = await scraper.scrape()
    print(f"Scraped {len(results)} properties. Deduplicating...")
    
    db = SessionLocal()
    try:
        stats = upsert_properties(db, results)
        print("Deduplication Stats:")
        print(stats)
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_xome_only())
