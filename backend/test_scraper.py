import asyncio
from scrapers.nationwide import NationwideScraper
from pprint import pprint

async def main():
    scraper = NationwideScraper()
    data = await scraper.scrape()
    pprint(data)
    print("Scrape complete.")

if __name__ == "__main__":
    asyncio.run(main())
