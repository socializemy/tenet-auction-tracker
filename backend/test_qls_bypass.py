import asyncio
from playwright.async_api import async_playwright

async def run():
    print("Starting playwright test...")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            print("Navigating to login...")
            await page.goto("https://www.qualityloan.com/QLSPortal/PagesPublic/Login.aspx", timeout=30000)
            
            print("Filling credentials...")
            await page.fill('input[id$="UserName"]', "CoJames1")
            await page.fill('input[id$="Password"]', "HJK4*#&90")
            
            print("Finding Login button...")
            # Use specific locator
            login_btn = page.locator('text="Login"').last
            if await login_btn.count() > 0:
                print("Clicking login button...")
                await login_btn.click(timeout=10000)
            else:
                print("Trying default press Enter ...")
                # Add no_wait_after to prevent playwright from hanging on navigation validation
                await page.press('input[id$="Password"]', 'Enter', no_wait_after=True)
            
            print("Waiting for page load state...")
            try:
                await page.wait_for_load_state("networkidle", timeout=10000)
                print("Network idle reached.")
            except Exception as e:
                print("Wait for load state timed out:", e)
            
            print("Accepting terms...")
            btn = page.locator('input[value="I Accept"], input[value="Accept"]')
            if await btn.count() > 0:
                await btn.first.click()
                await page.wait_for_timeout(3000)

            print("Testing JS bypass...")
            await page.evaluate("if(typeof Page_ValidationActive !== 'undefined') Page_ValidationActive = false;")
            await page.evaluate("if(typeof ValidatorEnable !== 'undefined') { for(var i=0; i<Page_Validators.length; i++) ValidatorEnable(Page_Validators[i], false); }")
            
            address_input = page.locator('input[id$="txtStreetAddress"]')
            if await address_input.count() > 0:
                await address_input.first.fill("Spokane")
                print("Filled 'Spokane' in Address.")
                
                print("Clicking search Submit...")
                submit_btn = page.locator('input[id$="cmdSubmitFileSearch"], input[value="Search"]')
                if await submit_btn.count() > 0:
                    await submit_btn.first.click(no_wait_after=True)
                else:
                    await address_input.first.press('Enter', no_wait_after=True)
                
                await page.wait_for_timeout(5000)
                await page.screenshot(path="qls_after_search.png")
                content = await page.content()
                if "No Records Found" in content:
                    print("Result: No Records Found for just 'Spokane'")
                else:
                    rows = await page.locator("table tr").count()
                    print(f"Result: Success! Found {rows} rows.")
            else:
                print("Could not find Address input box on File Search page.")
                
            await browser.close()
            print("Done gracefully.")
    except Exception as e:
        print(f"Exception caught in python: {e}")

if __name__ == "__main__":
    asyncio.run(run())
