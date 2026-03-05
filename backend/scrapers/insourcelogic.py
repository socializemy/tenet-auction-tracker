import logging
import csv
import os
from typing import List, Dict, Any

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

class InsourceLogicScraper(BaseScraper):
    """
    Offline CSV parser for Insource Logic properties.
    Due to a strict visual RadCaptcha intercepting authenticated traffic,
    this scraper reads from a manually downloaded export file in the backend/data directory.
    """
    def __init__(self):
        # We pass dummy URLs since it's an offline parser, but they help populate the DB source link
        super().__init__(
            source_name="Insource Logic",
            base_url="https://insourcelogic.com/SalesSearch.aspx"
        )
        self.data_filepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "insourcelogic_export.csv")

    async def scrape(self) -> List[Dict[str, Any]]:
        """
        Reads the local CSV export and maps it to the standard property list dictionary.
        Does not spin up Playwright instances.
        """
        logger.info(f"Starting OFFLINE scrape mapping for {self.source_name}")
        properties = []

        if not os.path.exists(self.data_filepath):
            logger.warning(f"{self.source_name}: Offline data file not found at {self.data_filepath}. "
                           "Please manually download the export and place it in the data directory.")
            return properties

        try:
            with open(self.data_filepath, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                # Check headers to ensure format isn't entirely broken
                headers = reader.fieldnames or []
                logger.info(f"{self.source_name}: Parsed headers: {headers}")

                # Standardize header lookup (case insensitive mapping)
                def get_val(row, possible_keys):
                    for key in possible_keys:
                        for row_key, row_val in row.items():
                            if row_key and key.lower() in row_key.lower():
                                return row_val.strip() if row_val else ""
                    return ""

                count = 0
                for row in reader:
                    count += 1
                    
                    # Extract fields mapping to multiple common header variations
                    tsn = get_val(row, ['TS Number', 'TS#', 'File Number', 'Reference'])
                    apn = get_val(row, ['APN', 'Parcel', 'Tax ID'])
                    address = get_val(row, ['Address', 'Property Address', 'Street'])
                    city = get_val(row, ['City'])
                    state = get_val(row, ['State'])
                    zip_code = get_val(row, ['Zip', 'Zip Code'])
                    county = get_val(row, ['County'])
                    
                    sale_date = get_val(row, ['Sale Date', 'Auction Date'])
                    sale_time = get_val(row, ['Sale Time', 'Time'])
                    
                    opening_bid_str = get_val(row, ['Opening Bid', 'Starting Bid', 'Bid Amount', 'Estimated Bid', 'NOS'])
                    status_raw = get_val(row, ['Status', 'Sale Status', 'State'])

                    # Filter strictly to Spokane bounds
                    if county.lower() != "spokane" and "spokane" not in city.lower():
                        continue
                        
                    if not address:
                         continue # Skip empty rows

                    # Default time format if none provided
                    if not sale_time:
                        sale_time = "10:00 AM"

                    # Parse numerical bids safely
                    starting_bid = 0.0
                    try:
                        clean_bid = opening_bid_str.replace('$', '').replace(',', '').strip()
                        if clean_bid and clean_bid != "0":
                            starting_bid = float(clean_bid)
                    except ValueError:
                        pass

                    # Status Rules mapping
                    status = "Active"
                    status_lower = status_raw.lower()
                    if "cancel" in status_lower:
                        status = "Cancelled"
                    elif "postpone" in status_lower:
                        status = "Postponed"
                    elif "sold" in status_lower:
                        status = "Sold"
                    elif "clear" in status_lower or "active" in status_lower:
                        status = "Active"

                    properties.append({
                        "source": self.source_name,
                        "tsn": tsn if tsn else f"IL-{count}",
                        "address": address,
                        "city": city,
                        "county": county if county else "Spokane",
                        "zip_code": zip_code,
                        "auction_date": sale_date,
                        "auction_time": sale_time,
                        "starting_bid": starting_bid,
                        "status": status,
                        "source_url": self.base_url,
                        "apn": apn if apn else None
                    })
                    
            logger.info(f"Insource Logic: Parsed {len(properties)} Spokane properties from offline CSV.")
            
        except Exception as e:
            logger.error(f"Error reading {self.source_name} CSV offline file: {e}")
            
        return properties
