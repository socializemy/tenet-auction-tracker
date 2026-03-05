"""
Nightly scheduler — runs all scrapers + dedup + Zillow enrichment at 2 AM PST.
Run this as a standalone process alongside uvicorn, or integrate into main.py startup.
"""
import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from run_scrapers import run_all_scrapers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    handlers=[
        logging.FileHandler("scrape.log"),
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)


async def scheduled_scrape():
    logger.info("⏰ Scheduled scrape starting...")
    await run_all_scrapers()
    logger.info("✅ Scheduled scrape complete")


async def main():
    scheduler = AsyncIOScheduler()
    # 2 AM Pacific Time (UTC-8 standard, UTC-7 daylight — use America/Los_Angeles)
    scheduler.add_job(
        scheduled_scrape,
        CronTrigger(hour=2, minute=0, timezone="America/Los_Angeles"),
        id="nightly_scrape",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started — nightly scrape at 2 AM Pacific")

    # Keep running indefinitely
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
