import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()
        
        target_url = "https://www.zillow.com/homes/1117-S-ASPEN-PL,-Spokane,-WA_rb/"
        print("Navigating to Zillow...")
        await page.goto(target_url, wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        
        content = await page.content()
        if "px-captcha" in content:
            print("CAPTCHA detected! Simulating Press & Hold...")
            
            # The div containing the captcha
            captcha_div = page.locator('#px-captcha')
            
            if await captcha_div.count():
                # Get the bounding box
                box = await captcha_div.bounding_box()
                if box:
                    # Move to center of the box
                    x = box['x'] + box['width'] / 2
                    y = box['y'] + box['height'] / 2
                    
                    print(f"Moving mouse to {x}, {y}")
                    await page.mouse.move(x, y)
                    await page.mouse.down()
                    
                    print("Holding for 10 seconds...")
                    await page.wait_for_timeout(10000)
                    await page.mouse.up()
                    
                    print("Released. Waiting for challenge to resolve...")
                    await page.wait_for_timeout(5000)
                    
                    new_content = await page.content()
                    if "px-captcha" in new_content:
                        print("Failed. Still on CAPTCHA page.")
                    else:
                        print("SUCCESS! CAPTCHA bypassed via mouse action.")
            else:
                print("Could not find #px-captcha div.")
        else:
            print("No CAPTCHA detected.")
            
        await browser.close()

asyncio.run(main())
