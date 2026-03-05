import asyncio
import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('TWOCAPTCHA_API_KEY', '7ed31552b003dd2a187e6414b341f174')

def test_api():
    app_id = "PXHYx10rg3"
    page_url = "https://www.zillow.com/homes/1117-S-ASPEN-PL,-Spokane,-WA_rb/"
    
    url = f"http://2captcha.com/in.php?key={API_KEY}&method=perimeterx&appId={app_id}&pageurl={page_url}&json=1"
    
    print(f"Sending GET request to: {url.replace(API_KEY, 'API_KEY')}")
    response = requests.get(url).json()
    print(f"Response: {response}")

if __name__ == "__main__":
    test_api()
