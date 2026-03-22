from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func
from pydantic import BaseModel
from typing import List, Optional
import json
import logging
import os
import shutil
import uuid
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

from database import Property, PropertyNote, PropertyPhoto, get_db, init_db
from run_scrapers import run_all_scrapers, get_scrape_status

# Directory for team-uploaded property photos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PHOTOS_DIR = os.path.join(BASE_DIR, "property_photos")
os.makedirs(PHOTOS_DIR, exist_ok=True)

app = FastAPI(title="Spokane Auction Properties API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded photos as static files
app.mount("/api/photos/files", StaticFiles(directory=PHOTOS_DIR), name="property_photos")


@app.on_event("startup")
def on_startup():
    init_db()


# ──────────────────────────────────────────
# Response / Request Models
# ──────────────────────────────────────────

class PropertyResponse(BaseModel):
    id: int
    tsn: Optional[str]
    source: str
    sources_list: Optional[str]
    source_urls: Optional[str]
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
    # Spokane County SCOUT assessor data
    assessed_value:      Optional[int]   = None
    assessed_land:       Optional[int]   = None
    assessed_building:   Optional[int]   = None
    owner_name:          Optional[str]   = None
    owner_address:       Optional[str]   = None
    annual_taxes:        Optional[int]   = None
    taxes_owing:         Optional[float] = None
    last_sale_price:     Optional[int]   = None
    last_sale_date:      Optional[str]   = None
    scout_legal:         Optional[str]   = None
    scout_parcel_class:  Optional[str]   = None
    scout_tca:           Optional[str]   = None
    scout_land_sqft:     Optional[int]   = None
    scout_house_type:    Optional[str]   = None
    scout_basement_sqft: Optional[int]   = None
    scout_garage_sqft:   Optional[int]   = None
    scout_sales:         Optional[str]   = None
    scout_permits:       Optional[str]   = None
    scout_fetched_at:    Optional[str]   = None
    last_seen_at: Optional[str]

    class Config:
        from_attributes = True


class NoteCreate(BaseModel):
    author: Optional[str] = "Team"
    body: str


class NoteResponse(BaseModel):
    id: int
    property_id: int
    author: str
    body: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class PhotoResponse(BaseModel):
    id: int
    property_id: int
    filename: str
    caption: Optional[str]
    uploaded_by: Optional[str]
    created_at: str
    url: str          # full path the frontend can use to display the image

    class Config:
        from_attributes = True


# ──────────────────────────────────────────
# Properties
# ──────────────────────────────────────────

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


# ──────────────────────────────────────────
# Notes
# ──────────────────────────────────────────

@app.get("/api/properties/{property_id}/notes", response_model=List[NoteResponse])
def get_notes(property_id: int, db: Session = Depends(get_db)):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    notes = (
        db.query(PropertyNote)
        .filter(PropertyNote.property_id == property_id)
        .order_by(PropertyNote.created_at.desc())
        .all()
    )
    for n in notes:
        n.created_at = n.created_at.isoformat() + "Z"
        n.updated_at = n.updated_at.isoformat() + "Z"
    return notes


@app.post("/api/properties/{property_id}/notes", response_model=NoteResponse, status_code=201)
def add_note(property_id: int, payload: NoteCreate, db: Session = Depends(get_db)):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    if not payload.body.strip():
        raise HTTPException(status_code=422, detail="Note body cannot be empty")
    note = PropertyNote(
        property_id=property_id,
        author=payload.author or "Team",
        body=payload.body.strip(),
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    note.created_at = note.created_at.isoformat() + "Z"
    note.updated_at = note.updated_at.isoformat() + "Z"
    return note


@app.delete("/api/properties/{property_id}/notes/{note_id}", status_code=204)
def delete_note(property_id: int, note_id: int, db: Session = Depends(get_db)):
    note = db.query(PropertyNote).filter(
        PropertyNote.id == note_id,
        PropertyNote.property_id == property_id,
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()


# ──────────────────────────────────────────
# Photos
# ──────────────────────────────────────────

@app.get("/api/properties/{property_id}/photos", response_model=List[PhotoResponse])
def get_photos(property_id: int, db: Session = Depends(get_db)):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    photos = (
        db.query(PropertyPhoto)
        .filter(PropertyPhoto.property_id == property_id)
        .order_by(PropertyPhoto.created_at.asc())
        .all()
    )
    result = []
    for p in photos:
        result.append(PhotoResponse(
            id=p.id,
            property_id=p.property_id,
            filename=p.filename,
            caption=p.caption,
            uploaded_by=p.uploaded_by,
            created_at=p.created_at.isoformat() + "Z",
            url=f"/api/photos/files/{p.filename}",
        ))
    return result


@app.post("/api/properties/{property_id}/photos", response_model=PhotoResponse, status_code=201)
async def upload_photo(
    property_id: int,
    file: UploadFile = File(...),
    caption: Optional[str] = Form(None),
    uploaded_by: Optional[str] = Form("Team"),
    db: Session = Depends(get_db),
):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    # Validate file type
    allowed = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=422, detail="Only JPEG, PNG, WebP, and GIF images are accepted")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "jpg"
    unique_name = f"{property_id}_{uuid.uuid4().hex}.{ext}"
    dest = os.path.join(PHOTOS_DIR, unique_name)

    with open(dest, "wb") as out:
        shutil.copyfileobj(file.file, out)

    photo = PropertyPhoto(
        property_id=property_id,
        filename=unique_name,
        caption=caption,
        uploaded_by=uploaded_by or "Team",
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)

    return PhotoResponse(
        id=photo.id,
        property_id=photo.property_id,
        filename=photo.filename,
        caption=photo.caption,
        uploaded_by=photo.uploaded_by,
        created_at=photo.created_at.isoformat() + "Z",
        url=f"/api/photos/files/{photo.filename}",
    )


@app.delete("/api/properties/{property_id}/photos/{photo_id}", status_code=204)
def delete_photo(property_id: int, photo_id: int, db: Session = Depends(get_db)):
    photo = db.query(PropertyPhoto).filter(
        PropertyPhoto.id == photo_id,
        PropertyPhoto.property_id == property_id,
    ).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    # Remove file from disk
    dest = os.path.join(PHOTOS_DIR, photo.filename)
    if os.path.exists(dest):
        os.remove(dest)
    db.delete(photo)
    db.commit()


# ──────────────────────────────────────────
# Scraper control
# ──────────────────────────────────────────

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
    return get_scrape_status()


# ──────────────────────────────────────────
# Stats
# ──────────────────────────────────────────

@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
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
