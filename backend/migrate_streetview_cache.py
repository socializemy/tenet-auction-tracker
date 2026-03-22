"""
One-time migration: download all Street View images that are currently stored
as Google API URLs in the DB and cache them locally.

Run after deploying the image-caching code:
  docker exec tenet-auction-tracker-backend-1 python3 /app/migrate_streetview_cache.py
"""
import hashlib
import os
import sqlite3
import time

import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STREETVIEW_DIR = os.path.join(BASE_DIR, "streetview_cache")
os.makedirs(STREETVIEW_DIR, exist_ok=True)

DB_PATH = "/app/data/auction_data.db"

conn = sqlite3.connect(DB_PATH)
rows = conn.execute(
    "SELECT id, address, city, image_url FROM properties WHERE image_url LIKE '%googleapis%'"
).fetchall()

print(f"Found {len(rows)} properties with Google Street View URLs to migrate...")

updated = 0
failed = 0

for prop_id, address, city, google_url in rows:
    city = city or "Spokane"
    state = "WA"
    addr_hash = hashlib.md5(f"{address},{city},{state}".lower().encode()).hexdigest()[:16]
    cache_file = os.path.join(STREETVIEW_DIR, f"sv_{addr_hash}.jpg")
    local_url = f"/api/streetview/sv_{addr_hash}.jpg"

    if os.path.exists(cache_file):
        # Already cached — just update the DB URL
        conn.execute("UPDATE properties SET image_url=? WHERE id=?", (local_url, prop_id))
        conn.commit()
        print(f"  [cached]  {address} → {local_url}")
        updated += 1
        continue

    try:
        resp = requests.get(google_url, timeout=15)
        if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image/"):
            with open(cache_file, "wb") as f:
                f.write(resp.content)
            conn.execute("UPDATE properties SET image_url=? WHERE id=?", (local_url, prop_id))
            conn.commit()
            print(f"  [OK]      {address} → {local_url}")
            updated += 1
        else:
            print(f"  [SKIP]    {address} — HTTP {resp.status_code} (no image at this location)")
            failed += 1
    except Exception as e:
        print(f"  [ERROR]   {address}: {e}")
        failed += 1

    time.sleep(0.5)  # gentle rate limit

conn.close()
print(f"\nDone. Updated: {updated}, Failed/skipped: {failed}")
print(f"Images cached in: {STREETVIEW_DIR}")
