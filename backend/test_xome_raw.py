import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def test():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            url = "https://www.xome.com/auctions/listing/WA/Spokane"
            print(f"Navigating to {url}")
            
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(8000)
            
            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find the element containing our known address from the screenshot
            address_nodes = soup.find_all(string=lambda text: "6203 N Wall St" in text if text else False)
            print(f"Nodes matching address: {len(address_nodes)}")
            
            for node in address_nodes:
                parent = node.parent
                for _ in range(15): # Go up 15 levels to find the card container
                    if parent:
                        print(f"Tag: {parent.name}, Class: {parent.get('class')}")
                        parent = parent.parent
                        
            await browser.close()
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test())
