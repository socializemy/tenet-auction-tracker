import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        )
        page = await context.new_page()

        query = "1117 S ASPEN PL, Spokane, WA site:redfin.com"
        print(f"Searching Google for: {query}")
        
        await page.goto(f"https://www.google.com/search?q={query.replace(' ', '+')}", wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        
        # Click the first Redfin result
        first_link = page.locator('a[href*="redfin.com/WA/Spokane"]').first
        if await first_link.count():
            url = await first_link.get_attribute('href')
            print(f"Found Redfin URL: {url}")
            await page.goto(url, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)
            
            img = await page.locator('.bp-Homecard__Photo--image, .img-card, .photoviewer-img').first.get_attribute('src') if await page.locator('.bp-Homecard__Photo--image, .img-card, .photoviewer-img').first.count() else "None"
            price_el = page.locator('.statsValue, [data-rf-test-id="abp-price"], .price').first
            price = await price_el.inner_text() if await price_el.count() else "None"
            
            print(f"Price: {price}")
            print(f"Image: {img}")
        else:
            print("No Redfin links found on Google.")
            
        await browser.close()

asyncio.run(main())
