import asyncio
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("https://spokesman.column.us/search")
        search = page.locator('input[placeholder*="Search"]').first
        await search.fill("Trustee Sale")
        await search.press("Enter")
        await page.wait_for_timeout(5000)
        card = await page.query_selector('div.public-notice-result')
        if card:
            print("--- INNER TEXT ---")
            print(await card.inner_text())
            print("--- TEXT CONTENT ---")
            print(await card.text_content())
        await browser.close()

asyncio.run(test())
