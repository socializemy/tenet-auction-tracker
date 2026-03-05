import asyncio
import os
from twocaptcha import TwoCaptcha
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('TWOCAPTCHA_API_KEY', '7ed31552b003dd2a187e6414b341f174')

async def main():
    solver = TwoCaptcha(API_KEY)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        target_url = "https://www.zillow.com/homes/1117-S-ASPEN-PL,-Spokane,-WA_rb/"
        print("Navigating to Zillow...")
        await page.goto(target_url, wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        
        content = await page.content()
        if "px-captcha" in content:
            print("CAPTCHA detected! Attempting to solve PerimeterX...")
            
            try:
                # Based on the debug HTML, the PerimeterX appId is 'PXHYx10rg3'
                # And the pageURL is the current URL
                
                print("Sending to 2Captcha...")
                # PerimeterX solving usually requires appId, pageurl, and sometimes custom params.
                # 2Captcha supports PerimeterX via the PerimeterX method (or generic token methods).
                
                # Let's try the official 2captcha python method for PerimeterX
                result = solver.perimeterx(
                    app_id='PXHYx10rg3',
                    pageurl=target_url,
                    # Zillow usually doesn't need custom params but sometimes needs vid
                )
                
                print(f"Token received: {result['code'][:30]}...")
                
                # Inject the token back into the page.
                # PerimeterX usually accepts the token via a specific callback or cookie.
                # For Zillow, setting the _px cookie often works if it's a cookie-based challenge.
                # It might also be possible to just inject it into the challenge form if there is one.
                print("Setting _px3 cookie with token...")
                await context.add_cookies([{
                    "name": "_px3",
                    "value": result['code'],
                    "domain": ".zillow.com",
                    "path": "/"
                }])
                
                print("Reloading page with solved cookie...")
                await page.reload(wait_until="domcontentloaded")
                await page.wait_for_timeout(4000)
                
                new_content = await page.content()
                if "px-captcha" in new_content:
                    print("Still blocked after reloading with token.")
                else:
                    print("Successfully bypassed CAPTCHA on reload!")
                    
            except Exception as e:
                print(f"Error solving CAPTCHA: {e}")
                
        else:
            print("No CAPTCHA detected.")
            
        await browser.close()

asyncio.run(main())
