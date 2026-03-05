import asyncio
from playwright.async_api import async_playwright

async def test_search():
    address = "1117 S ASPEN PL"
    query = f"{address} Spokane WA house exterior"
    print(f"\n--- Testing Google Images High Res: {query} ---")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.goto(f"https://www.google.com/search?tbm=isch&q={query.replace(' ', '+')}", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        
        # Wait for thumbnails to load
        await page.wait_for_timeout(3000)
        
        # Get page content and extract image URLs via regex
        content = await page.content()
        import re
        
        # Find all https URLs ending in jpg, jpeg, or webp
        # Google embeds the high-res URLs in script tags
        urls = re.findall(r'(https?://[^"\\]+?\.(?:jpg|jpeg|png|webp))', content)
        
        # Filter and clean up URLs
        valid_urls = []
        for u in urls:
            # Clean up escaped chars just in case
            u = u.replace('\\u003d', '=').replace('\\u0026', '&')
            if 'gstatic' not in u and 'favicon' not in u and 'profile' not in u:
                valid_urls.append(u)
                
        # deduplicate maintaining order
        seen = set()
        unique_urls = []
        for u in valid_urls:
            if u not in seen:
                seen.add(u)
                unique_urls.append(u)
                
        if unique_urls:
            print(f"Found {len(unique_urls)} candidate high-res URLs.")
            for i, url in enumerate(unique_urls[:5]):
                print(f"[{i}] {url}")
        else:
            print("No high-res URLs found.")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_search())
