import re
import logging
from typing import List, Dict, Any

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

BASE_URL = "https://clearrecon-wa.com/washington-listings/"
SOURCE_NAME = "Clear Recon WA"


class ClearReconScraper:
    def __init__(self):
        self.source_name = SOURCE_NAME
        self.base_url = BASE_URL

    async def scrape(self) -> List[Dict[str, Any]]:
        logger.info(f"Starting HTTP scrape for {self.source_name}")
        properties = []

        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=30,
            verify=False,
            headers=HEADERS,
        ) as client:
            # Step 1: hit the page — if there is a disclaimer cookie it is set
            # on the GET response; following the redirect chain handles it.
            try:
                resp = await client.get(self.base_url)
                resp.raise_for_status()
            except Exception as e:
                logger.error(f"ClearRecon: initial GET failed: {e}")
                return properties

            html = resp.text

            # If a disclaimer/agree wall is present, click through it by
            # submitting the agree link as a GET with the same session.
            if "agree" in html.lower() and "posts-data-table" not in html.lower():
                logger.info("ClearRecon: disclaimer detected, accepting...")
                soup_wall = BeautifulSoup(html, "html.parser")
                agree_link = soup_wall.find("a", string=re.compile(r"agree", re.I))
                if agree_link and agree_link.get("href"):
                    href = agree_link["href"]
                    agree_url = href if href.startswith("http") else f"https://clearrecon-wa.com{href}"
                    try:
                        resp = await client.get(agree_url)
                        resp.raise_for_status()
                        html = resp.text
                    except Exception as e:
                        logger.warning(f"ClearRecon: agree click failed: {e}")

        soup = BeautifulSoup(html, "html.parser")

        # DataTables renders ALL rows in the initial HTML (client-side mode).
        # The visible "show N entries" only hides rows via CSS — all <tr> are present.
        table = soup.select_one("table.posts-data-table")
        if not table:
            # Fallback: try any table with recognisable trustee-sale columns
            table = soup.find("table")

        if not table:
            logger.warning("ClearRecon: no table found in page HTML")
            return properties

        rows = table.select("tbody tr")
        logger.info(f"ClearRecon: found {len(rows)} raw rows")

        for row in rows:
            try:
                row_text = row.get_text(" ", strip=True)
                if "spokane" not in row_text.lower():
                    continue

                cells = row.find_all("td")
                if len(cells) < 5:
                    continue

                tsn = cells[0].get_text(strip=True)
                address_full = cells[1].get_text(strip=True)
                sale_date = cells[2].get_text(strip=True)
                sale_time = cells[3].get_text(strip=True)

                # Parse "8525 N Weipert Dr, Spokane WA, 99208" style
                parts = [p.strip() for p in address_full.split(",")]
                address = parts[0] if parts else address_full

                city = "Spokane"
                if len(parts) > 1:
                    city_part = parts[1].strip()
                    if city_part.upper().endswith("WA"):
                        city = city_part[:-2].strip()
                    else:
                        city = city_part
                if "SPOKANE VALLEY" in address_full.upper():
                    city = "Spokane Valley"
                elif "SPOKANE" in address_full.upper():
                    city = "Spokane"

                # Grab detail URL from TSN cell link if present
                source_url = self.base_url
                link = cells[0].find("a")
                if link and link.get("href"):
                    href = link["href"]
                    source_url = href if href.startswith("http") else f"https://clearrecon-wa.com{href}"

                if tsn and address:
                    properties.append({
                        "source": self.source_name,
                        "tsn": tsn,
                        "address": address,
                        "city": city,
                        "county": "Spokane",
                        "zip_code": parts[2].strip() if len(parts) > 2 else "",
                        "auction_date": sale_date,
                        "auction_time": sale_time,
                        "starting_bid": 0.0,
                        "status": "Active",
                        "source_url": source_url,
                    })
            except Exception as e:
                logger.warning(f"ClearRecon row error: {e}")
                continue

        logger.info(f"ClearRecon WA: scraped {len(properties)} Spokane properties")
        return properties
