import asyncio
from playwright.async_api import async_playwright

async def test_search(address, p):
    query = f"{address} Spokane WA house exterior"
    
    browser = await p.chromium.launch(headless=True)
    context = await browser.new_context()
    page = await context.new_page()
    
    print(f"Testing Google Images for: {address}")
    await page.goto(f"https://www.google.com/search?tbm=isch&q={query.replace(' ', '+')}", wait_until="domcontentloaded")
    await page.wait_for_timeout(3000)
    
    # Ignore svg and gstatic icons
    img_el = page.locator('img[src^="http"]:not([src$=".svg"]):not([src*="gstatic.com/s/i/"])').nth(1)
    
    if await img_el.count():
        img_src = await img_el.get_attribute('src')
        print(f"Found Image 2: {img_src}")
    
    # Try looking for actual result thumbnails (often base64 or encrypted-tbn0)
    images = await page.locator('img').all()
    for img in images[:15]:
        src = await img.get_attribute('src')
        if src and ('encrypted-tbn0' in src or src.startswith('data:image/jpeg')):
            print(f"Found Real Result Image: {src[:100]}...")
            break
            
    await browser.close()

async def main():
    async with async_playwright() as p:
        await test_search("1875 N. Willamette Rd.", p)

asyncio.run(main())
