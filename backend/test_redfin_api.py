import requests
import json

def test_redfin():
    address = "1117 S ASPEN PL Spokane WA"
    url = f"https://www.redfin.com/stingray/do/location-autocomplete?location={address.replace(' ', '+')}&v=2"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    print(f"Testing Redfin Autocomplete for {address}...")
    try:
        response = requests.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        # Redfin returns JSON starting with {}&&
        content = response.text
        if content.startswith("{}&&"):
            content = content[4:]
            
        data = json.loads(content)
        print("Success! Data:")
        # Look for Exact match
        for row in data.get('payload', {}).get('exactMatch', {}).get('rows', []):
            if 'url' in row:
                print(f"Found URL: {row['url']}")
                print(f"Found Price/Value: {row.get('price')}")
                
        for row in data.get('payload', {}).get('sections', [])[0].get('rows', []):
             if 'url' in row:
                print(f"Found Section URL: {row['url']}")
                
    except Exception as e:
        print(f"Error: {e}")
        try:
            print(f"Response: {response.text[:500]}")
        except:
            pass

if __name__ == "__main__":
    test_redfin()
