"""
Shared image caching utility.
Downloads a remote image URL and stores it in streetview_cache/ so it can
be served by FastAPI's StaticFiles mount at /api/streetview/<filename>.
"""
import hashlib
import os
from typing import Optional

import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "streetview_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "image/webp,image/*,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.google.com/",
}


def addr_hash(address: str, city: str, state: str = "WA") -> str:
    return hashlib.md5(f"{address},{city},{state}".lower().encode()).hexdigest()[:16]


def download_and_cache(img_url: str, prefix: str, address: str, city: str, state: str = "WA") -> Optional[str]:
    """
    Download img_url and save as {prefix}_{hash}.jpg in CACHE_DIR.
    Returns the local /api/streetview/... URL on success, None on failure.
    Skips download if the file already exists.
    """
    if not img_url or not img_url.startswith("http"):
        return None
    h = addr_hash(address, city, state)
    cache_file = os.path.join(CACHE_DIR, f"{prefix}_{h}.jpg")
    local_url = f"/api/streetview/{prefix}_{h}.jpg"

    if os.path.exists(cache_file):
        return local_url

    try:
        resp = requests.get(img_url, headers=BROWSER_HEADERS, timeout=12, stream=True)
        ct = resp.headers.get("content-type", "")
        if resp.status_code == 200 and ct.startswith("image/"):
            with open(cache_file, "wb") as f:
                for chunk in resp.iter_content(8192):
                    f.write(chunk)
            return local_url
    except Exception:
        pass
    return None
