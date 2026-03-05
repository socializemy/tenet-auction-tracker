from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func
from pydantic import BaseModel
from typing import List, Optional
import json
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

from database import Property, get_db, init_db
from run_scrapers import run_all_scrapers, get_scrape_status

app = FastAPI(title="Spokane Auction Properties API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


# --- Response Models ---
class PropertyResponse(BaseModel):
    id: int
    tsn: Optional[str]
    source: str
    sources_list: Optional[str]  # JSON
    source_urls: Optional[str]   # JSON
    address: str
    city: str
    county: str
    zip_code: Optional[str]
    auction_date: Optional[str]
    auction_time: Optional[str]
    starting_bid: float
    estimated_value: Optional[float]
    status: str
    zillow_url: Optional[str]
    image_url: Optional[str]
    bedrooms: Optional[float]
    bathrooms: Optional[float]
    square_feet: Optional[int]
    lot_size: Optional[str]
    property_type: Optional[str]
    year_built: Optional[int]
    apn: Optional[str]
    last_seen_at: Optional[str]

    class Config:
        from_attributes = True


# --- Endpoints ---

@app.get("/api/properties", response_model=List[PropertyResponse])
def get_properties(
    county: Optional[str] = None,
    city: Optional[str] = None,
    sort_by: Optional[str] = "auction_date",
    min_bid: Optional[float] = None,
    max_bid: Optional[float] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Property)

    if county:
        query = query.filter(Property.county.ilike(f"%{county}%"))
    if city:
        query = query.filter(Property.city.ilike(f"%{city}%"))
    if min_bid is not None:
        query = query.filter(Property.starting_bid >= min_bid)
    if max_bid is not None:
        query = query.filter(Property.starting_bid <= max_bid)

    if sort_by == "auction_date":
        query = query.order_by(Property.auction_date.asc())
    elif sort_by == "starting_bid":
        query = query.order_by(Property.starting_bid.asc())
    elif sort_by == "estimated_value":
        query = query.order_by(Property.estimated_value.desc())

    results = query.all()
    # Convert datetime fields to string for response
    for r in results:
        if r.last_seen_at:
            r.last_seen_at = r.last_seen_at.isoformat() + "Z"
    return results


@app.get("/api/properties/{property_id}", response_model=PropertyResponse)
def get_property(property_id: int, db: Session = Depends(get_db)):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    if prop.last_seen_at:
        prop.last_seen_at = prop.last_seen_at.isoformat() + "Z"
    return prop


@app.post("/api/trigger-scrape")
async def trigger_scrape(background_tasks: BackgroundTasks):
    """Manually trigger a full scrape + dedup + Zillow enrichment."""
    status = get_scrape_status()
    if status.get("running"):
        return {"message": "Scrape already in progress", "status": status}

    background_tasks.add_task(run_all_scrapers)
    return {"message": "Scrape triggered — running in background"}


@app.get("/api/scrape-status")
def scrape_status():
    """Returns the status of the last/current scrape run."""
    return get_scrape_status()


@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    """Summary statistics for the dashboard."""
    total = db.query(Property).count()
    by_source = (
        db.query(Property.source, sa_func.count(Property.id))
        .group_by(Property.source)
        .all()
    )
    by_city = (
        db.query(Property.city, sa_func.count(Property.id))
        .group_by(Property.city)
        .all()
    )
    return {
        "total_properties": total,
        "by_source": {s: c for s, c in by_source},
        "by_city": {c: n for c, n in by_city},
    }
