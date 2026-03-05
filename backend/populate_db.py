import asyncio
from datetime import datetime
from database import SessionLocal, Property
from scrapers.nationwide import NationwideScraper
from sqlalchemy.orm import Session
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_date(date_str: str):
    try:
        return datetime.strptime(date_str, "%m/%d/%Y").date()
    except ValueError:
        return None

def save_properties(db: Session, properties: list):
    count = 0
    for p in properties:
        # Simple upsert logic based on TS Number or Address + Date
        # For simplicity, we'll just check if address exists
        existing = db.query(Property).filter(Property.address == p['address']).first()
        
        # Try to parse price if available, here we don't have starting bid yet 
        # but could parse it from status if 'Sold back to beneficiary for: $294,175.00'
        starting_bid = 0.0
        status = p['status']
        if "Sold back" in status and "$" in status:
            try:
                price_str = status.split("$")[1].replace(",", "").split()[0]
                starting_bid = float(price_str)
            except:
                pass
                
        auction_date = parse_date(p['auction_date'])
        
        if existing:
            # Update
            existing.status = status
            existing.auction_date = auction_date
            existing.auction_time = p['auction_time']
            if starting_bid > 0:
                existing.starting_bid = starting_bid
        else:
            # Insert
            new_prop = Property(
                source=p['source'],
                address=p['address'],
                city=p['city'],
                county=p['county'],
                zip_code="",
                auction_date=auction_date,
                auction_time=p['auction_time'],
                starting_bid=starting_bid,
                status=status
            )
            db.add(new_prop)
        count += 1
        
    db.commit()
    logger.info(f"Saved {count} properties to database.")

async def run_scrapers():
    db = SessionLocal()
    try:
        scrapers = [NationwideScraper()]
        all_properties = []
        for scraper in scrapers:
            data = await scraper.scrape()
            all_properties.extend(data)
            
        save_properties(db, all_properties)
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_scrapers())
