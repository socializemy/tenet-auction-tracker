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

BASE_URL = "https://elitepostandpub.com/index.php"
SOURCE_NAME = "Elite Post & Pub"


class ElitePostScraper:
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
            # Try WA-filtered URL first (common PHP query param pattern)
            urls_to_try = [
                f"{self.base_url}?state=WA",
                f"{self.base_url}?State=WA",
                self.base_url,
            ]

            html = None
            for url in urls_to_try:
                try:
                    resp = await client.get(url)
                    resp.raise_for_status()
                    if "spokane" in resp.text.lower() or "washington" in resp.text.lower():
                        html = resp.text
                        logger.info(f"Elite Post: got content from {url}")
                        break
                except Exception as e:
                    logger.warning(f"Elite Post: GET {url} failed: {e}")

            if not html:
                logger.error("Elite Post: could not retrieve any useful page")
                return properties

        soup = BeautifulSoup(html, "html.parser")
        rows = soup.find_all(["tr", "li"], class_=re.compile(r"notice|listing|property|row", re.I))
        if not rows:
            rows = soup.find_all("tr")

        logger.info(f"Elite Post: found {len(rows)} raw rows")

        for row in rows:
            try:
                row_text = row.get_text(" ", strip=True)
                if "spokane" not in row_text.lower():
                    continue

                cells = row.find_all("td")
                if len(cells) < 2:
                    continue

                texts = [c.get_text(strip=True) for c in cells]

                tsn = ""
                address = ""
                sale_date = ""
                status = "Active"

                for t in texts:
                    if re.match(r"\d{2}/\d{2}/\d{4}", t) and not sale_date:
                        sale_date = t
                    elif re.match(r"\d+\s+\w+", t) and not address:
                        address = t
                    elif re.match(r"WA-\d+|\d{4}-\d+", t) and not tsn:
                        tsn = t

                if not address and texts:
                    address = next(
                        (t for t in texts if re.search(r"\d+\s+\w+\s+(st|ave|rd|dr|blvd|way|ln|ct|pl)", t, re.I)),
                        texts[0] if texts else "",
                    )

                city = "Spokane Valley" if "Spokane Valley" in row_text else "Spokane"

                link = row.find("a")
                source_url = ""
                if link and link.get("href"):
                    href = link["href"]
                    source_url = href if href.startswith("http") else f"https://elitepostandpub.com/{href.lstrip('/')}"

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
                        "status": status,
                        "source_url": source_url or self.base_url,
                    })
            except Exception as e:
                logger.warning(f"Elite Post row error: {e}")

        logger.info(f"Elite Post & Pub: scraped {len(properties)} Spokane properties")
        return properties
