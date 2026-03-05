import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("Navigating to login...")
        await page.goto("https://www.qualityloan.com/QLSPortal/PagesPublic/Login.aspx", timeout=30000)
        
        print("Filling credentials...")
        await page.fill('input[name*="UserName"]', "CoJames1")
        await page.fill('input[name*="Password"]', "HJK4*#&90")
        
        print("Clicking login...")
        login_btn = page.locator('input[type="submit"], button:has-text("Login"), a#submitLoginBtn')
        if await login_btn.count() > 0:
            await login_btn.first.click()
            await page.wait_for_timeout(5000)
        else:
            print("Could not find login button!")
            return
            
        print("After login wait, Url is:", page.url)
        content = await page.content()
        await page.screenshot(path="qls_after_login.png")
        if "Invalid login" in content or "Login failed" in content:
            print("Login failed with invalid credentials.")
            
        if "Terms" in content or "Accept" in content:
            print("Terms modal or page detected. Clicking accept...")
            btn = page.locator('input[value="I Accept"], input[value="Accept"]')
            if await btn.count() > 0:
                await btn.first.click()
                await page.wait_for_timeout(3000)
            print("After Accept, Url is:", page.url)
            await page.screenshot(path="qls_after_accept.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
