"""
Street View cache recovery: re-download images for all properties whose
image_url points to /api/streetview/... but the file is missing on disk.

Also handles the original migration case (googleapis URLs in the DB).

Run after a container rebuild wipes the cache:
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
API_KEY = os.environ.get("GOOGLE_STREET_VIEW_API_KEY", "")

if not API_KEY:
    print("ERROR: GOOGLE_STREET_VIEW_API_KEY not set — aborting.")
    exit(1)

conn = sqlite3.connect(DB_PATH)

# Case 1: image_url is still a raw googleapis URL (original migration)
googleapis_rows = conn.execute(
    "SELECT id, address, city, image_url FROM properties WHERE image_url LIKE '%googleapis%'"
).fetchall()

# Case 2: image_url points to local cache but file is missing on disk
cached_rows = conn.execute(
    "SELECT id, address, city, image_url FROM properties WHERE image_url LIKE '/api/streetview/%'"
).fetchall()
missing_rows = [
    (pid, addr, city, img)
    for pid, addr, city, img in cached_rows
    if not os.path.exists(os.path.join(STREETVIEW_DIR, os.path.basename(img)))
]

print(f"Found {len(googleapis_rows)} properties with raw googleapis URLs.")
print(f"Found {len(missing_rows)} properties with missing cache files.")

updated = 0
failed = 0


def fetch_and_cache(prop_id, address, city, google_url=None):
    global updated, failed
    city = city or "Spokane"
    state = "WA"
    addr_hash = hashlib.md5(f"{address},{city},{state}".lower().encode()).hexdigest()[:16]
    cache_file = os.path.join(STREETVIEW_DIR, f"sv_{addr_hash}.jpg")
    local_url = f"/api/streetview/sv_{addr_hash}.jpg"

    if os.path.exists(cache_file):
        conn.execute("UPDATE properties SET image_url=? WHERE id=?", (local_url, prop_id))
        conn.commit()
        print(f"  [cached]  {address}")
        updated += 1
        return

    url = google_url or (
        f"https://maps.googleapis.com/maps/api/streetview"
        f"?size=600x400&location={requests.utils.quote(f'{address}, {city}, {state}')}"
        f"&key={API_KEY}"
    )

    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image/"):
            with open(cache_file, "wb") as f:
                f.write(resp.content)
            conn.execute("UPDATE properties SET image_url=? WHERE id=?", (local_url, prop_id))
            conn.commit()
            print(f"  [OK]      {address} → {local_url}")
            updated += 1
        else:
            print(f"  [SKIP]    {address} — HTTP {resp.status_code}")
            failed += 1
    except Exception as e:
        print(f"  [ERROR]   {address}: {e}")
        failed += 1

    time.sleep(0.3)


for prop_id, address, city, google_url in googleapis_rows:
    fetch_and_cache(prop_id, address, city, google_url)

for prop_id, address, city, _ in missing_rows:
    fetch_and_cache(prop_id, address, city)

conn.close()
print(f"\nDone. Cached/updated: {updated}, Failed/skipped: {failed}")
print(f"Images in: {STREETVIEW_DIR}")
