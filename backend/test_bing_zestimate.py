import asyncio
from playwright.async_api import async_playwright
import re

async def test_search():
    address = "1117 S ASPEN PL"
    query = f"{address} Spokane WA zillow"
    print(f"\n--- Testing Zestimate via Bing: {query} ---")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        await page.goto(f"https://www.bing.com/search?q={query.replace(' ', '+')}", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        
        # Extract search result titles and snippets
        content = await page.content()
        
        if "captcha" in content.lower() and "bing" not in content.lower():
            print("Hit a captcha on Bing as well.")
            
        results = await page.locator('li.b_algo').all()
        for i, res in enumerate(results[:5]):
            try:
                title = await res.locator('h2').inner_text()
                snippet = await res.locator('.b_caption p, .b_algoSlug').inner_text()
                print(f"Result {i+1}:")
                print(f"Title: {title}")
                print(f"Snippet: {snippet}")
                
                # Check for Zestimate or price
                combined = title + " " + snippet
                # look for Zestimate then a price
                zmatches = re.findall(r'(?:Zestimate|Estimated value).*?\$([0-9,]+)', combined, re.IGNORECASE)
                if zmatches:
                    print(f"--> Found Zestimate! ${zmatches[0]}")
                else:
                    prices = re.findall(r'\$([0-9,]+)', combined)
                    if prices:
                        print(f"--> Found generic price: ${prices[0]}")
                        
                print("-" * 40)
            except Exception as e:
                pass
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_search())
