import asyncio
from playwright.async_api import async_playwright
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        url = "https://www.spokesman.com/classifieds/search/legal-notices/?q=Notice+of+Trustee%27s+Sale"
        logger.info(f"Navigating to {url}")
        await page.goto(url)
        await page.wait_for_timeout(5000)
        
        content = await page.content()
        with open("spokesman_debug.html", "w") as f:
            f.write(content)
            
        logger.info("Saved HTML to spokesman_debug.html")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test())
