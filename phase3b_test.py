import os
import re
import sys
import time
import requests

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

if not PEXELS_API_KEY:
    print("❌ PEXELS_API_KEY is missing.")
    sys.exit(1)

PEXELS_URL = "https://api.pexels.com/v1/search"

HEADERS = {
    "Authorization": PEXELS_API_KEY
}

# ---------------------------------------------------------
# PHASE 3B
# Pexels-only video search and download test
#
# NO GEMINI
# NO TELEGRAM
# NO LTX
#
# Purpose:
# 1. Search Pexels
# 2. Select suitable vertical videos
# 3. Download them
# 4. Save them for the next phase
# ---------------------------------------------------------

SEARCHES = [
    "business money finance",
    "person shopping",
    "business office",
    "money saving",
    "technology business"
]

OUTPUT_DIR = "phase3b_clips"
os.makedirs(OUTPUT_DIR, exist_ok=True)

MAX_CLIPS = 5
DOWNLOAD_TIMEOUT = 25


def search_pexels(query):
    print(f"\n🔎 Searching Pexels: {query}")

    params = {
        "query": query,
        "per_page": 10,
        "orientation": "portrait"
    }

    try:
        response = requests.get(
            PEXELS_URL,
            headers=HEADERS,
            params=params,
            timeout=15
        )

        print(f"   HTTP status: {response.status_code}")

        if response.status_code != 200:
            print(f"❌ Pexels error: {response.text[:500]}")
            return []

        data = response.json()

        videos = data.get("photos", [])

        print(f"   Found {len(videos)} photos.")

        return videos

    except requests.exceptions.Timeout:
        print("❌ Pexels search timed out.")
        return []

    except Exception as e:
        print(f"❌ Pexels search failed: {e}")
        return []


def download_image(photo, number):
    try:
        src = photo.get("src", {})

        # Prefer large image
        image_url = (
            src.get("large2x")
            or src.get("large")
            or src.get("original")
        )

        if not image_url:
            print("❌ No image URL found.")
            return False

        filename = os.path.join(
            OUTPUT_DIR,
            f"clip_{number:02d}.jpg"
        )

        print(f"⬇️ Downloading clip {number}...")

        response = requests.get(
            image_url,
            timeout=DOWNLOAD_TIMEOUT,
            stream=True
        )

        if response.status_code != 200:
            print(
                f"❌ Download failed: HTTP {response.status_code}"
            )
            return False

        with open(filename, "wb") as file:
            for chunk in response.iter_content(8192):
                if chunk:
                    file.write(chunk)

        size = os.path.getsize(filename)

        if size < 1000:
            os.remove(filename)
            print("❌ File was too small.")
            return False

        print(
            f"✅ Saved {filename} "
            f"({size:,} bytes)"
        )

        return True

    except requests.exceptions.Timeout:
        print("❌ Download timed out.")
        return False

    except Exception as e:
        print(f"❌ Download error: {e}")
        return False


def main():

    print("=" * 60)
    print("🎬 SIXSCONTENT — PHASE 3B")
    print("PEXELS MEDIA COLLECTION TEST")
    print("=" * 60)

    print("\n✅ Pexels API key detected.")
    print("🚫 Gemini disabled in Phase 3B.")
    print("🚫 Telegram disabled in Phase 3B.")
    print("🚫 LTX disabled in Phase 3B.")

    downloaded = 0
    used_ids = set()

    for query in SEARCHES:

        if downloaded >= MAX_CLIPS:
            break

        photos = search_pexels(query)

        for photo in photos:

            if downloaded >= MAX_CLIPS:
                break

            photo_id = photo.get("id")

            if photo_id in used_ids:
                continue

            used_ids.add(photo_id)

            success = download_image(
                photo,
                downloaded + 1
            )

            if success:
                downloaded += 1

            time.sleep(0.5)

    print("\n" + "=" * 60)
    print("PHASE 3B RESULT")
    print("=" * 60)

    print(f"✅ Clips downloaded: {downloaded}")
    print(f"📁 Folder: {OUTPUT_DIR}")

    if downloaded == 0:
        print("\n❌ No media was downloaded.")
        sys.exit(1)

    if downloaded < MAX_CLIPS:
        print(
            f"\n⚠️ Only {downloaded}/{MAX_CLIPS} "
            "clips were downloaded."
        )
    else:
        print(
            "\n🔥 PHASE 3B SUCCESS!"
        )

    print("\nFiles:")
    for filename in sorted(os.listdir(OUTPUT_DIR)):
        path = os.path.join(OUTPUT_DIR, filename)
        size = os.path.getsize(path)
        print(f"  • {filename} — {size:,} bytes")

    print("\nGitHub will now stop automatically.")
    print("No 24/7 process is running.")


if __name__ == "__main__":
    main()
