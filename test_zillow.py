import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "sec-ch-ua": '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"'
            }
        )
        page = await context.new_page()
        # hide webdriver
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        print("Navigating...")
        await page.goto("https://www.zillow.com/homes/1117-S-ASPEN-PL,-Spokane,-WA_rb/", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        
        content = await page.content()
        if "px-captcha" in content:
            print("FAILED: Caught by CAPTCHA again.")
            await page.wait_for_timeout(5000) # Give time to visually inspect
        else:
            print("SUCCESS: Bypassed CAPTCHA!")
        await browser.close()

asyncio.run(main())
