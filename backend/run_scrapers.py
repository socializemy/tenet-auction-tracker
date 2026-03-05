"""
Runs all scrapers, deduplicates results, and enriches with Zillow data.
Called by the scheduler and the /api/trigger-scrape API endpoint.
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict

from database import SessionLocal, init_db, Property
from deduplication import upsert_properties
from zillow_enricher import enrich_properties_zillow

from scrapers.nationwide import NationwideScraper
from scrapers.quality_loan import QualityLoanScraper
from scrapers.clearrecon import ClearReconScraper
from scrapers.auction_com import AuctionComScraper
from scrapers.xome import XomeScraper
from scrapers.elitepostandpub import ElitePostScraper
from scrapers.aztectrustee import AztecTrusteeScraper
from scrapers.stoxposting import StoxPostingScraper
from scrapers.servicelinkasap import ServiceLinkScraper
from scrapers.insourcelogic import InsourceLogicScraper

logger = logging.getLogger(__name__)

SCRAPERS = [
    NationwideScraper,
    QualityLoanScraper,
    ClearReconScraper,
    AuctionComScraper,
    XomeScraper,
    ElitePostScraper,
    AztecTrusteeScraper,
    StoxPostingScraper,
    ServiceLinkScraper,
    InsourceLogicScraper,
]

# Global state for scrape status
_last_scrape_status: Dict = {
    "last_run": None,
    "running": False,
    "results": {},
    "error": None,
}


def get_scrape_status() -> Dict:
    return _last_scrape_status


async def run_all_scrapers(enrich_zillow: bool = True) -> Dict:
    global _last_scrape_status

    if _last_scrape_status["running"]:
        return {"error": "Scrape already in progress"}

    _last_scrape_status["running"] = True
    _last_scrape_status["error"] = None
    init_db()

    all_properties = []
    per_source_counts = {}

    for ScraperClass in SCRAPERS:
        scraper = ScraperClass()
        try:
            logger.info(f"Running scraper: {scraper.source_name}")
            results = await scraper.scrape()
            per_source_counts[scraper.source_name] = len(results)
            all_properties.extend(results)
            logger.info(f"{scraper.source_name}: {len(results)} properties found")
        except Exception as e:
            logger.error(f"Scraper {scraper.source_name} failed: {e}")
            per_source_counts[scraper.source_name] = 0

    # Deduplicate and upsert into DB
    db = SessionLocal()
    try:
        dedup_stats = upsert_properties(db, all_properties)

        # Zillow enrichment for unenriched properties
        if enrich_zillow:
            from sqlalchemy import or_
            unenriched = db.query(Property).filter(
                Property.zillow_url.is_(None)
            ).limit(200).all()  # Increased limit so newly scraped pipelines get fully parsed
            zillow_count = await enrich_properties_zillow(db, unenriched)
        else:
            zillow_count = 0

    finally:
        db.close()

    result = {
        "last_run": datetime.utcnow().isoformat() + "Z",
        "running": False,
        "total_scraped": len(all_properties),
        "dedup_stats": dedup_stats,
        "zillow_enriched": zillow_count,
        "per_source": per_source_counts,
        "error": None,
    }
    _last_scrape_status.update(result)
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_all_scrapers())
