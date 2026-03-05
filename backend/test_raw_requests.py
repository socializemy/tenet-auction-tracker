import requests
import re
from bs4 import BeautifulSoup

def test_raw_search():
    address = "1117 S ASPEN PL"
    query = f"{address} Spokane WA zillow".replace(" ", "+")
    
    url = f"https://html.duckduckgo.com/html/?q={query}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    print(f"--- Testing Raw DDG Search: {query} ---")
    
    try:
        req = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {req.status_code}")
        
        soup = BeautifulSoup(req.text, 'html.parser')
        
        for res in soup.find_all('div', class_='result'):
            title_elem = res.find('h2', class_='result__title')
            desc_elem = res.find('a', class_='result__snippet')
            
            title = title_elem.text.strip() if title_elem else ""
            desc = desc_elem.text.strip() if desc_elem else ""
            
            print(f"Title: {title}")
            print(f"Desc: {desc}")
            
            combined = title + " " + desc
            zmatches = re.findall(r'(?:Zestimate|Estimated value|price.*?changed to|Est\. Value).*?\$([0-9,]+)', combined, re.IGNORECASE)
            if zmatches:
                print(f"--> Found Value! ${zmatches[0]}")
            else:
                prices = re.findall(r'\$([0-9,]+)', combined)
                if prices:
                    print(f"--> Found generic price: ${prices[0]}")
            print("-" * 40)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_raw_search()
