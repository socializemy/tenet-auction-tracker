import asyncio
from playwright.async_api import async_playwright

async def test():
    print("Testing Xome Direct URL...")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            url = "https://www.xome.com/auctions/listing/WA/Spokane-County"
            print(f"Navigating to {url}")
            
            # Use 'domcontentloaded' to avoid waiting for every single tracking pixel to load
            response = await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            print("Page loaded, waiting 5 seconds for React to mount cards...")
            await page.wait_for_timeout(5000)
            
            status = response.status if response else "Unknown"
            print("Response status:", status)
            title = await page.title()
            print("Page title:", title)
            
            cards = await page.locator('div.property-card, a.property-link, [class*="PropertyCard"], [class*="listingCard"], article').count()
            print(f"Cards found directly: {cards}")
            
            await page.screenshot(path="xome_direct_test.png", full_page=True)
            await browser.close()
            print("Done gracefully.")
    except Exception as e:
        print(f"FATAL ASYNC EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(test())
    except Exception as e:
        print(f"FATAL TOP EXCEPTION: {e}")
