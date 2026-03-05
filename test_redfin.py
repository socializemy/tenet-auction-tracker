import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        )
        page = await context.new_page()

        print("Navigating Redfin...")
        # Redfin search URL format
        await page.goto("https://www.redfin.com/city/17151/WA/Spokane/filter/status=active+contingent+pending,include=sold-6mo", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        
        # Look for search box and type
        await page.fill('input[id="search-box-input"]', "1117 S ASPEN PL, Spokane, WA")
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(4000)
        
        content = await page.content()
        with open("redfin_debug.html", "w") as f:
            f.write(content)
        print("Saved to redfin_debug.html")

        # Try to find price and image
        price = await page.locator('.statsValue').first.inner_text() if await page.locator('.statsValue').first.count() else "None"
        img = await page.locator('.img-card').first.get_attribute('src') if await page.locator('.img-card').first.count() else "None"
        
        print(f"Price: {price}")
        print(f"Image: {img}")
        
        await browser.close()

asyncio.run(main())
