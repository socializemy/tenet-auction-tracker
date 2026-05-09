"""
Backfill zillow_photo_url for all properties missing it.
Priority: Zillow (curl_cffi TLS impersonation) → Realtor.com (DDG search) → skip.

  docker exec tenet-auction-tracker-backend-1 python3 /app/backfill_zillow_photos.py
"""
import os
import sqlite3
import sys
import time

# Make sure the app directory is on the path so we can import image_cache etc.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from zillow_enricher import _fetch_zillow_photo, _fetch_realtor_photo, _CFFI_AVAILABLE

DB_PATH = "/app/data/auction_data.db"

conn = sqlite3.connect(DB_PATH)

# Ensure column exists
existing_cols = {r[1] for r in conn.execute("PRAGMA table_info(properties)").fetchall()}
if "zillow_photo_url" not in existing_cols:
    conn.execute("ALTER TABLE properties ADD COLUMN zillow_photo_url TEXT")
    conn.commit()
    print("Added zillow_photo_url column.")

rows = conn.execute(
    "SELECT id, address, city, zillow_url FROM properties "
    "WHERE zillow_photo_url IS NULL OR zillow_photo_url = ''"
).fetchall()

print(f"curl_cffi available: {_CFFI_AVAILABLE}")
print(f"Found {len(rows)} properties to backfill...\n")

ok = 0
failed = 0

for prop_id, address, city, zillow_url in rows:
    city = city or "Spokane"
    local_url = None

    # 1. Try Zillow
    if zillow_url:
        local_url = _fetch_zillow_photo(zillow_url, address, city)
        if local_url:
            print(f"  [Zillow]    {address} → {local_url}")

    # 2. Try Realtor.com via DDG
    if not local_url:
        local_url = _fetch_realtor_photo(address, city)
        if local_url:
            print(f"  [Realtor]   {address} → {local_url}")

    if local_url:
        conn.execute("UPDATE properties SET zillow_photo_url=? WHERE id=?", (local_url, prop_id))
        conn.commit()
        ok += 1
    else:
        print(f"  [SKIP]      {address} — no photo found")
        failed += 1

    time.sleep(1.0)

conn.close()
print(f"\nDone. Cached: {ok}, Failed/skipped: {failed}")
