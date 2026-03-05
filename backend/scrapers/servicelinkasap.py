from typing import List, Dict, Any
from scrapers.base import BaseScraper
import logging
import re

logger = logging.getLogger(__name__)

class ServiceLinkScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            source_name="ServiceLink ASAP",
            base_url="https://www.servicelinkasap.com/quicksearch.aspx"
        )
        
    async def scrape(self) -> List[Dict[str, Any]]:
        """
        Main method to trigger scraping.
        Must return a list of dictionaries where each dictionary 
        represents a property.
        """
        logger.info(f"Starting offline scrape mapping for {self.source_name}")
        properties = []
        import os
        html_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "servicelinkasap_export.html")
        
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extract just the HTML table part from the markdown
            if "```html" in content:
                table_html = content.split("```html")[1].split("```")[0]
            else:
                table_html = content
                
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(table_html, 'html.parser')
            rows = soup.find_all('tr')
            
            logger.info(f"ServiceLink: found {len(rows)} potential table rows in offline dump")
            for row in rows:
                try:
                    cells = row.find_all('td')
                    if len(cells) < 16:
                        continue  # Not a standard property row
                        
                    texts = [c.get_text(strip=True) for c in cells]
                    
                    sale_date_raw = texts[0]
                    asap_id = texts[1]
                    ts_number = texts[2]
                    address = texts[3]
                    city = texts[4]
                    state = texts[5]
                    zip_code = texts[6]
                    county = texts[7]
                    apn = texts[8]
                    status_raw = texts[9]
                    nos_amt = texts[10]
                    open_bid_amt = texts[11]
                    sold_amt = texts[12]
                    sale_location = texts[13]
                    
                    # Filter out non-Spokane if the search boundaries leaked
                    if "Spokane" not in county and "Spokane" not in city and "Spokane" not in address:
                        continue
                        
                    # Parse Date/Time
                    sale_date = ""
                    sale_time = "10:00 AM"
                    if " " in sale_date_raw:
                        parts = sale_date_raw.split(" ", 1)
                        sale_date = parts[0]
                        sale_time = parts[1]
                    else:
                        sale_date = sale_date_raw

                    # Parse Bid Amounts
                    starting_bid = 0.0
                    try:
                        open_bid_str = open_bid_amt.replace('$', '').replace(',', '').strip()
                        if open_bid_str and open_bid_str != "0" and open_bid_str != "0.00":
                             starting_bid = float(open_bid_str)
                        else:
                             nos_str = nos_amt.replace('$', '').replace(',', '').strip()
                             if nos_str and nos_str != "0":
                                 starting_bid = float(nos_str)
                    except ValueError:
                        pass

                    # Derive Status Rules
                    status = "Active"
                    status_lower = status_raw.lower()
                    if "cancel" in status_lower:
                        status = "Cancelled"
                    elif "postpone" in status_lower:
                        status = "Postponed"
                    elif "sold" in status_lower:
                        status = "Sold"

                    if address:
                        properties.append({
                            "source": self.source_name,
                            "tsn": ts_number,
                            "address": address,
                            "city": city,
                            "county": county,
                            "zip_code": zip_code,
                            "auction_date": sale_date,
                            "auction_time": sale_time,
                            "starting_bid": starting_bid,
                            "status": status,
                            "source_url": self.base_url,
                            "apn": apn if apn and "Unknown" not in apn else None
                        })
                except Exception as e:
                    logger.warning(f"ServiceLink row error: {e}")

            logger.info(f"ServiceLink ASAP: scraped {len(properties)} Spokane properties")
            
        except Exception as e:
            logger.error(f"Error reading offline html dump: {e}")
            
        return properties

            

