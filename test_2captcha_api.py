import asyncio
import os
import time
import requests
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('TWOCAPTCHA_API_KEY', '7ed31552b003dd2a187e6414b341f174')

async def solve_px(api_key, page_url, app_id):
    print("Submitting PerimeterX to 2Captcha API...")
    url = f"http://2captcha.com/in.php?key={api_key}&method=perimeterx&appId={app_id}&pageurl={page_url}&json=1"
    response = requests.get(url).json()
    if response.get("status") != 1:
        raise Exception(f"Failed to submit: {response}")
        
    request_id = response.get("request")
    print(f"Submitted. ID: {request_id}. Waiting for solution...")
    
    # Poll for result
    poll_url = f"http://2captcha.com/res.php?key={api_key}&action=get&id={request_id}&json=1"
    
    for _ in range(24): # Wait up to 2 minutes (24 * 5 seconds)
        await asyncio.sleep(5)
        res = requests.get(poll_url).json()
        if res.get("status") == 1:
            return res.get("request")
        elif res.get("request") == "CAPCHA_NOT_READY":
            print("Not ready yet...")
            continue
        else:
            raise Exception(f"Error checking status: {res}")
            
    raise Exception("Timeout waiting for CAPTCHA solution")

async def main():
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
                # Based on the debug HTML, Zillow appId is often 'PXHYx10rg3'
                # Extract actual appId from the page if possible
                app_id = "PXHYx10rg3"
                if "window._pxAppId = '" in content:
                    app_id = content.split("window._pxAppId = '")[1].split("'")[0]
                    print(f"Extracted Dynamic App ID: {app_id}")
                
                token = await solve_px(API_KEY, target_url, app_id)
                print(f"Token received! Prefix snippet: {token[:30]}...")
                
                print("Setting _px3 cookie with token...")
                await context.add_cookies([{
                    "name": "_px3",
                    "value": token,
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
