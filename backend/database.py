import os
import json
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
default_db_path = os.path.join(BASE_DIR, "auction_data.db")
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{default_db_path}")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    tsn = Column(String, nullable=True, index=True)        # Trustee Sale Number (dedup key)
    source = Column(String, index=True)                    # Primary source that found this
    source_urls = Column(String, default="[]")             # JSON list of all source URLs
    sources_list = Column(String, default="[]")            # JSON list of all source names
    address = Column(String)
    city = Column(String, index=True)
    county = Column(String, index=True)
    zip_code = Column(String, nullable=True)
    auction_date = Column(String, nullable=True, index=True)
    auction_time = Column(String, nullable=True)
    starting_bid = Column(Float, default=0.0)
    estimated_value = Column(Float, nullable=True)
    bedrooms = Column(Float, nullable=True)
    bathrooms = Column(Float, nullable=True)
    square_feet = Column(Integer, nullable=True)
    lot_size = Column(String, nullable=True)
    property_type = Column(String, nullable=True)
    year_built = Column(Integer, nullable=True)
    apn = Column(String, nullable=True)
    status = Column(String, default="Active")
    zillow_url = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    last_seen_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PropertyNote(Base):
    """Team-visible notes attached to a property."""
    __tablename__ = "property_notes"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    author = Column(String, nullable=False, default="Team")
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PropertyPhoto(Base):
    """Team-uploaded photos for a property."""
    __tablename__ = "property_photos"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String, nullable=False)       # stored filename on disk
    caption = Column(String, nullable=True)
    uploaded_by = Column(String, nullable=True, default="Team")
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
