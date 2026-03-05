"""
Quickly pushes ONLY the Insource Logic records into the database.
"""
import asyncio
import logging

from database import SessionLocal, init_db
from deduplication import upsert_properties
from scrapers.insourcelogic import InsourceLogicScraper

logging.basicConfig(level=logging.INFO)

async def run_insource_only():
    init_db()
    scraper = InsourceLogicScraper()
    results = await scraper.scrape()
    
    db = SessionLocal()
    try:
        dedup_stats = upsert_properties(db, results)
        print("Upsert Stats:", dedup_stats)
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_insource_only())
