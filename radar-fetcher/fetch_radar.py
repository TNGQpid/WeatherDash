import os
import time
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import imageio
from io import BytesIO
from glob import glob

# Shared volume
OUTPUT_DIR = "/data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Fetch interval in seconds (default 15 minutes)
INTERVAL = int(os.getenv("FETCH_INTERVAL", 900))

# Regions and NOAA sector codes
REGIONS = {
    "East": "eus",
    "Great Lakes": "cgl",
    "Midwest": "umv"
}

# --- Cleanup step: remove stale files for old region names ---
valid_regions = set(REGIONS.keys())
for file in os.listdir(OUTPUT_DIR):
    if file.endswith(".gif") or file.endswith(".jpg"):
        # region is everything before "_" or "." in filename
        region_name = file.split("_")[0].split(".")[0]
        if region_name not in valid_regions:
            os.remove(os.path.join(OUTPUT_DIR, file))
            print(f"[{datetime.now()}] Removed stale file {file}", flush=True)

# Base URL template
BASE_URL = "https://cdn.star.nesdis.noaa.gov/GOES19/ABI/SECTOR/{sector}/GEOCOLOR/"

# Number of frames to keep for GIF (1 for every 2 seconds?)
FRAMES_TO_KEEP = 100

def get_latest_image_urls(sector):
    """Scrape NOAA folder and return sorted latest image URLs (1000x1000 or 1200x1200)."""
    url = BASE_URL.format(sector=sector)
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        urls = []
        for a in soup.find_all("a"):
            href = a.get("href")
            if href and (href.endswith("1000x1000.jpg") or href.endswith("1200x1200.jpg")):
                urls.append(url + href)
        urls.sort()
        return urls[-FRAMES_TO_KEEP:]
    except Exception as e:
        print(f"[{datetime.now()}] Error fetching image list for {sector}: {e}", flush=True)
        return []

def download_image(url, out_path):
    try:
        r = requests.get(url, timeout=15, stream=True)
        r.raise_for_status()
        with open(out_path, "wb") as f:
            f.write(r.content)
        print(f"[{datetime.now()}] Saved {out_path}", flush=True)
    except Exception as e:
        print(f"[{datetime.now()}] Error downloading {url}: {e}", flush=True)

def build_gif(region):
    """Build GIF from downloaded images."""
    files = sorted(glob(f"{OUTPUT_DIR}/{region}_*.jpg"))
    if not files:
        return
    frames = [imageio.imread(f) for f in files]
    gif_path = f"{OUTPUT_DIR}/{region}.gif"
    imageio.mimsave(gif_path, frames, duration=0.3)
    print(f"[{datetime.now()}] Built GIF {gif_path} with {len(frames)} frames", flush=True)

def cleanup_old_frames(region):
    """Remove old images beyond FRAMES_TO_KEEP."""
    files = sorted(glob(f"{OUTPUT_DIR}/{region}_*.jpg"))
    if len(files) > FRAMES_TO_KEEP:
        for f in files[:-FRAMES_TO_KEEP]:
            os.remove(f)

while True:
    for region, sector in REGIONS.items():
        urls = get_latest_image_urls(sector)
        for url in urls:
            timestamp = url.split("/")[-1].split("_")[0]
            out_file = f"{OUTPUT_DIR}/{region}_{timestamp}.jpg"
            if not os.path.exists(out_file):
                download_image(url, out_file)
        cleanup_old_frames(region)
        build_gif(region)
    time.sleep(INTERVAL)