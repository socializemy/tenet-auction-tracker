import asyncio
from playwright.async_api import async_playwright

async def test_search(address, p):
    query = f"{address}, Spokane, WA"
    print(f"\n--- Testing: {query} ---")
    
    browser = await p.chromium.launch(headless=True)
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    page = await context.new_page()
    
    await page.goto("https://www.redfin.com/", wait_until="domcontentloaded")
    await page.wait_for_timeout(2000)
    
    await page.fill('input[name="searchInputBox"]', query)
    await page.wait_for_timeout(2000)
    await page.keyboard.press("Enter")
    await page.wait_for_timeout(5000)
    
    current_url = page.url
    print(f"Landed on: {current_url}")
    
    # Check if we got to a property page
    price_el = page.locator('.statsValue, [data-rf-test-id="abp-price"], .price').first
    price = await price_el.inner_text() if await price_el.count() else "None"
    
    img_el = page.locator('.bp-Homecard__Photo--image, .img-card, .photoviewer-img, img.Image.img-responsive').first
    img = await img_el.get_attribute('src') if await img_el.count() else "None"
    
    print(f"Found Price: {price}")
    print(f"Found Image: {img}")
    
    await browser.close()

async def main():
    async with async_playwright() as p:
        await test_search("1117 S ASPEN PL", p)
        await test_search("1875 N. Willamette Rd.", p)
        await test_search("3718/3720 S PHOEBE ST", p)

asyncio.run(main())
