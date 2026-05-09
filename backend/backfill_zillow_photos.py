"""
One-time backfill: fetch Zillow og:image for all properties that have a
zillow_url but no zillow_photo_url yet.

  docker exec tenet-auction-tracker-backend-1 python3 /app/backfill_zillow_photos.py
"""
import hashlib
import os
import sqlite3
import time

import requests
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STREETVIEW_DIR = os.path.join(BASE_DIR, "streetview_cache")
os.makedirs(STREETVIEW_DIR, exist_ok=True)

DB_PATH = "/app/data/auction_data.db"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

conn = sqlite3.connect(DB_PATH)

# Add column if it doesn't exist
existing_cols = {r[1] for r in conn.execute("PRAGMA table_info(properties)").fetchall()}
if "zillow_photo_url" not in existing_cols:
    conn.execute("ALTER TABLE properties ADD COLUMN zillow_photo_url TEXT")
    conn.commit()
    print("Added zillow_photo_url column.")

rows = conn.execute(
    "SELECT id, address, city, zillow_url FROM properties "
    "WHERE zillow_url IS NOT NULL AND (zillow_photo_url IS NULL OR zillow_photo_url = '')"
).fetchall()

print(f"Found {len(rows)} properties to backfill...")

ok = 0
failed = 0

for prop_id, address, city, zillow_url in rows:
    city = city or "Spokane"
    state = "WA"
    addr_hash = hashlib.md5(f"{address},{city},{state}".lower().encode()).hexdigest()[:16]
    cache_file = os.path.join(STREETVIEW_DIR, f"zillow_{addr_hash}.jpg")
    local_url = f"/api/streetview/zillow_{addr_hash}.jpg"

    if os.path.exists(cache_file):
        conn.execute("UPDATE properties SET zillow_photo_url=? WHERE id=?", (local_url, prop_id))
        conn.commit()
        print(f"  [cached]  {address}")
        ok += 1
        continue

    try:
        resp = requests.get(zillow_url, headers=HEADERS, timeout=12)
        if resp.status_code != 200:
            print(f"  [SKIP]    {address} — Zillow HTTP {resp.status_code}")
            failed += 1
            time.sleep(1)
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        og = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "og:image"})
        img_url = og.get("content", "") if og else ""

        if not img_url or not img_url.startswith("http"):
            print(f"  [NO IMG]  {address} — no og:image found")
            failed += 1
            time.sleep(1)
            continue

        img_resp = requests.get(img_url, headers=HEADERS, timeout=12)
        if img_resp.status_code == 200 and img_resp.headers.get("content-type", "").startswith("image/"):
            with open(cache_file, "wb") as f:
                f.write(img_resp.content)
            conn.execute("UPDATE properties SET zillow_photo_url=? WHERE id=?", (local_url, prop_id))
            conn.commit()
            print(f"  [OK]      {address} → {local_url}")
            ok += 1
        else:
            print(f"  [SKIP]    {address} — image download failed (HTTP {img_resp.status_code})")
            failed += 1

    except Exception as e:
        print(f"  [ERROR]   {address}: {e}")
        failed += 1

    time.sleep(1.5)  # be polite

conn.close()
print(f"\nDone. Cached: {ok}, Failed/skipped: {failed}")
