import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.quality_loan import QualityLoanScraper
import logging

logging.basicConfig(level=logging.INFO)

async def test():
    try:
        os.environ["QUALITY_LOAN_USER"] = "CoJames1"
        os.environ["QUALITY_LOAN_PASS"] = "HJK4*#&90"
        
        print("Initializing Quality Loan Scraper...")
        scraper = QualityLoanScraper()
        
        print("Running scrape...")
        results = await scraper.scrape()
        
        print(f"Scraped {len(results)} properties.")
        for i, res in enumerate(results[:3]):
            print(f"[{i+1}] {res['address']} | {res['auction_date']} | Status: {res['status']}")
    except Exception as e:
        print(f"FATAL EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(test())
    except Exception as e:
        print(f"FATAL ASYNCIO EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
