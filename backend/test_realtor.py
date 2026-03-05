import asyncio
from playwright.async_api import async_playwright

async def test_search(p):
    address = "1117 S ASPEN PL"
    query = f"{address} Spokane WA".replace(" ", "%20")
    
    browser = await p.chromium.launch(headless=True)
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    page = await context.new_page()
    
    print(f"Testing Realtor.com...")
    # Realtor has a direct search endpoint
    await page.goto(f"https://www.realtor.com/realestateandhomes-detail/{address.replace(' ', '-')}_Spokane_WA", wait_until="domcontentloaded")
    await page.wait_for_timeout(4000)
    
    print("URL:", page.url)
    
    img_el = page.locator('img.carousel-photo, .hero-image img, img[alt*="property"]').first
    img = await img_el.get_attribute('src') if await img_el.count() else "None"
    
    price_el = page.locator('.price, [data-testid="price"]').first
    price = await price_el.inner_text() if await price_el.count() else "None"
    
    print(f"Price: {price}")
    print(f"Image: {img}")
    
    content = await page.content()
    with open("realtor_debug.html", "w") as f:
        f.write(content)
        
    await browser.close()

async def main():
    async with async_playwright() as p:
        await test_search(p)

asyncio.run(main())
