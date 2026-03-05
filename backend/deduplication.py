"""
Deduplication logic for merging scraper results.

Dedup strategy (priority order):
1. Trustee Sale Number (TSN) — most reliable cross-site key
2. Normalized address + auction_date fingerprint
"""
import json
import re
import logging
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from database import Property

logger = logging.getLogger(__name__)


def normalize_address(address: str) -> str:
    """Normalize an address string for fuzzy matching."""
    addr = address.upper().strip()
    # Expand common abbreviations
    replacements = {
        r'\bST\b': 'STREET', r'\bAVE\b': 'AVENUE', r'\bRD\b': 'ROAD',
        r'\bDR\b': 'DRIVE', r'\bBLVD\b': 'BOULEVARD', r'\bLN\b': 'LANE',
        r'\bCT\b': 'COURT', r'\bPL\b': 'PLACE', r'\bWAY\b': 'WAY',
        r'\bN\b': 'NORTH', r'\bS\b': 'SOUTH', r'\bE\b': 'EAST', r'\bW\b': 'WEST',
    }
    for pattern, repl in replacements.items():
        addr = re.sub(pattern, repl, addr)
    # Remove punctuation and extra spaces
    addr = re.sub(r'[^\w\s]', '', addr)
    addr = re.sub(r'\s+', ' ', addr).strip()
    return addr


def parse_date(date_str: str) -> str:
    """Try to parse a date string, return ISO format YYYY-MM-DD or raw string."""
    if not date_str:
        return ""
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y", "%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return date_str.strip()


def fingerprint(prop: Dict[str, Any]) -> str:
    """Generate a dedup fingerprint for a property dict."""
    addr = normalize_address(prop.get("address", ""))
    date = parse_date(prop.get("auction_date", ""))
    return f"{addr}|{date}"


def upsert_properties(db: Session, scraped: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Merge scraped property list into the database.
    Returns stats: {"inserted": N, "updated": N, "merged_sources": N}
    """
    stats = {"inserted": 0, "updated": 0, "merged_sources": 0}

    for prop in scraped:
        if not prop.get("address"):
            continue

        tsn = prop.get("tsn", "").strip()
        fp = fingerprint(prop)
        source = prop.get("source", "Unknown")
        source_url = prop.get("source_url", "")

        # --- Try to find existing record ---
        existing: Property | None = None

        if tsn:
            existing = db.query(Property).filter(Property.tsn == tsn).first()

        if not existing:
            # Match by fingerprint: check all existing records
            all_props = db.query(Property).all()
            for p in all_props:
                p_fp = fingerprint({
                    "address": p.address,
                    "auction_date": p.auction_date,
                })
                if p_fp == fp:
                    existing = p
                    break

        auction_date_iso = parse_date(prop.get("auction_date", ""))

        if existing:
            # Merge source info
            try:
                sources_list = json.loads(existing.sources_list or "[]")
                source_urls = json.loads(existing.source_urls or "[]")
            except Exception:
                sources_list, source_urls = [], []

            changed = False
            if source not in sources_list:
                sources_list.append(source)
                existing.sources_list = json.dumps(sources_list)
                changed = True

            if source_url and source_url not in source_urls:
                source_urls.append(source_url)
                existing.source_urls = json.dumps(source_urls)
                changed = True

            # Update TSN if we now have one
            if tsn and not existing.tsn:
                existing.tsn = tsn
                changed = True

            # Update bid if we got a non-zero value
            if prop.get("starting_bid", 0) > 0 and existing.starting_bid == 0:
                existing.starting_bid = prop["starting_bid"]
                changed = True

            # Update image if we have one
            if prop.get("image_url") and not existing.image_url:
                existing.image_url = prop["image_url"]
                changed = True

            existing.last_seen_at = datetime.utcnow()

            if changed:
                stats["merged_sources"] += 1
            else:
                stats["updated"] += 1

        else:
            # Insert new record
            new_prop = Property(
                tsn=tsn or None,
                source=source,
                source_urls=json.dumps([source_url] if source_url else []),
                sources_list=json.dumps([source]),
                address=prop.get("address", ""),
                city=prop.get("city", "Spokane"),
                county=prop.get("county", "Spokane"),
                zip_code=prop.get("zip_code", ""),
                auction_date=auction_date_iso or prop.get("auction_date", ""),
                auction_time=prop.get("auction_time", ""),
                starting_bid=float(prop.get("starting_bid", 0)),
                status=prop.get("status", "Active"),
                image_url=prop.get("image_url"),
                last_seen_at=datetime.utcnow(),
            )
            db.add(new_prop)
            stats["inserted"] += 1

    db.commit()
    logger.info(f"Dedup complete: {stats}")
    return stats
