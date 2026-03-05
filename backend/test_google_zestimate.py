import asyncio
from playwright.async_api import async_playwright
import re

async def test_search():
    address = "1117 S ASPEN PL"
    query = f"{address} Spokane WA zillow"
    print(f"\n--- Testing Zestimate via Google: {query} ---")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.goto(f"https://www.google.com/search?q={query.replace(' ', '+')}", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        
        # Extract search result titles and snippets
        content = await page.content()
        print(content[:2000]) # Print first 2000 chars to see if it's a captcha
        
        # Also try to grab all text on the page
        text = await page.evaluate('document.body.innerText')
        print("\n\n--- TEXT ---")
        print(text[:2000])
        
        # Try finding price in text
        prices = re.findall(r'\$([0-9,]+)', text)
        if prices:
            print(f"Found Prices in text: {prices}")
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_search())
