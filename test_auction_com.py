import asyncio
import sys
import logging
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)

async def test_scraper():
    print("Testing Auction.com...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        print("Navigating...")
        await page.goto("https://www.auction.com/residential/wa/spokane-county/", wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(5000)
        
        print("Saving HTML...")
        content = await page.content()
        with open("auction_com_page.html", "w", encoding="utf-8") as f:
            f.write(content)
            
        print("Done. Saved to auction_com_page.html")
        await browser.close()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_scraper())
