import asyncio
from database import SessionLocal, Property
from zillow_enricher import enrich_properties_zillow

async def main():
    db = SessionLocal()
    # Get properties that either lack estimate data or lack the newly added fields
    # But to be safe and get full data for all, we can just grab all properties
    properties = db.query(Property).all()
    
    print(f"Starting retroactive enrichment for {len(properties)} properties...")
    enriched_count = await enrich_properties_zillow(db, properties)
    print(f"Successfully enriched {enriched_count} properties.")
    db.close()

if __name__ == "__main__":
    asyncio.run(main())
