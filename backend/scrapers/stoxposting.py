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

BASE_URL = "https://www.stoxposting.com/"
SOURCE_NAME = "Stox Posting"


class StoxPostingScraper:
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
            try:
                resp = await client.get(self.base_url)
                resp.raise_for_status()
                html = resp.text
                soup = BeautifulSoup(html, "html.parser")
            except Exception as e:
                logger.error(f"Stox Posting: initial GET failed: {e}")
                return properties

            # Follow Washington link if present
            wa_link = soup.find(
                "a",
                string=re.compile(r"washington", re.I),
            ) or soup.find("a", href=re.compile(r"WA|washington", re.I))

            if wa_link and wa_link.get("href"):
                href = wa_link["href"]
                wa_url = href if href.startswith("http") else f"https://www.stoxposting.com/{href.lstrip('/')}"
                try:
                    resp = await client.get(wa_url)
                    resp.raise_for_status()
                    html = resp.text
                    soup = BeautifulSoup(html, "html.parser")
                    logger.info(f"Stox: followed WA link to {wa_url}")
                except Exception as e:
                    logger.warning(f"Stox: WA link follow failed: {e}")

            # Follow Spokane link if present
            spokane_link = soup.find("a", string=re.compile(r"spokane", re.I))
            if spokane_link and spokane_link.get("href"):
                href = spokane_link["href"]
                spokane_url = href if href.startswith("http") else f"https://www.stoxposting.com/{href.lstrip('/')}"
                try:
                    resp = await client.get(spokane_url)
                    resp.raise_for_status()
                    html = resp.text
                    soup = BeautifulSoup(html, "html.parser")
                    logger.info(f"Stox: followed Spokane link to {spokane_url}")
                except Exception as e:
                    logger.warning(f"Stox: Spokane link follow failed: {e}")

        rows = soup.find_all("tr")
        if not rows:
            rows = soup.find_all(class_=re.compile(r"listing|notice|property|row", re.I))

        logger.info(f"Stox Posting: found {len(rows)} raw rows")

        for row in rows:
            try:
                row_text = row.get_text(" ", strip=True)
                if "spokane" not in row_text.lower():
                    continue

                cells = row.find_all("td")
                if not cells:
                    continue

                texts = [c.get_text(strip=True) for c in cells]

                tsn = ""
                address = ""
                sale_date = ""

                for t in texts:
                    if re.match(r"\d{2}/\d{2}/\d{4}", t) and not sale_date:
                        sale_date = t
                    elif re.match(r"\d+\s+\w+", t) and not address:
                        address = t
                    elif re.match(r"WA-\d+|\d{4}-\d+", t) and not tsn:
                        tsn = t

                if not address:
                    address = next(
                        (t for t in texts if re.search(r"\d+\s+\w+\s+(st|ave|rd|dr|blvd|way|ln|ct|pl)", t, re.I)),
                        "",
                    )

                city = "Spokane Valley" if "Spokane Valley" in row_text else "Spokane"

                link = row.find("a")
                source_url = ""
                if link and link.get("href"):
                    href = link["href"]
                    source_url = href if href.startswith("http") else f"https://www.stoxposting.com/{href.lstrip('/')}"

                if address:
                    properties.append({
                        "source": self.source_name,
                        "tsn": tsn,
                        "address": address,
                        "city": city,
                        "county": "Spokane",
                        "zip_code": "",
                        "auction_date": sale_date,
                        "auction_time": "10:00 AM",
                        "starting_bid": 0.0,
                        "status": "Active",
                        "source_url": source_url or self.base_url,
                    })
            except Exception as e:
                logger.warning(f"Stox Posting row error: {e}")

        logger.info(f"Stox Posting: scraped {len(properties)} Spokane properties")
        return properties
