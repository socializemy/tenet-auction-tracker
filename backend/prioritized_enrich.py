import asyncio
from database import SessionLocal, Property
from zillow_enricher import enrich_properties_zillow

async def main():
    db = SessionLocal()
    # Grab the first 5 active properties to quickly populate data for testing
    properties = db.query(Property).filter(Property.status == 'Active').limit(5).all()
    
    print(f"Starting prioritized enrichment for {len(properties)} properties...")
    enriched_count = await enrich_properties_zillow(db, properties)
    print(f"Successfully enriched {enriched_count} properties.")
    db.close()

if __name__ == "__main__":
    asyncio.run(main())
