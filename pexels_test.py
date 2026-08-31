import os
import sys
import requests
from pathlib import Path

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

if not PEXELS_API_KEY:
    print("❌ PEXELS_API_KEY is missing.")
    sys.exit(1)

API_URL = "https://api.pexels.com/videos/search"

OUTPUT_DIR = Path("pexels_test_clips")
OUTPUT_DIR.mkdir(exist_ok=True)

SEARCHES = [
    "movie theater popcorn",
    "person choosing food",
    "shopping receipt",
]

headers = {
    "Authorization": PEXELS_API_KEY
}


def search_pexels(query):
    print(f"\n🔎 Searching Pexels: {query}")

    params = {
        "query": query,
        "orientation": "portrait",
        "size": "medium",
        "per_page": 5,
    }

    response = requests.get(
        API_URL,
        headers=headers,
        params=params,
        timeout=30
    )

    print(f"HTTP status: {response.status_code}")

    if response.status_code != 200:
        print("❌ Pexels API error:")
        print(response.text)
        return None

    data = response.json()

    videos = data.get("videos", [])

    if not videos:
        print("⚠️ No videos found.")
        return None

    return videos[0]


def choose_video_file(video):
    files = video.get("video_files", [])

    if not files:
        return None

    # Prefer portrait files and reasonable resolution.
    portrait_files = [
        f for f in files
        if f.get("width", 0) < f.get("height", 0)
    ]

    candidates = portrait_files if portrait_files else files

    # Prefer a file around 720p or lower to keep GitHub downloads reasonable.
    candidates.sort(
        key=lambda f: (
            abs((f.get("height") or 0) - 1280),
            -(f.get("width") or 0)
        )
    )

    return candidates[0]


def download_video(video, index):
    video_file = choose_video_file(video)

    if not video_file:
        print("❌ No downloadable video file found.")
        return False

    download_url = video_file.get("link")

    if not download_url:
        print("❌ Video has no download URL.")
        return False

    output_file = OUTPUT_DIR / f"scene_{index}.mp4"

    print(f"🎬 Downloading scene {index}")
    print(f"Resolution: {video_file.get('width')}x{video_file.get('height')}")

    try:
        with requests.get(
            download_url,
            stream=True,
            timeout=120
        ) as response:

            response.raise_for_status()

            with open(output_file, "wb") as file:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        file.write(chunk)

        size_mb = output_file.stat().st_size / (1024 * 1024)

        print(f"✅ Saved: {output_file}")
        print(f"📦 Size: {size_mb:.2f} MB")

        return True

    except Exception as error:
        print(f"❌ Download failed: {error}")

        if output_file.exists():
            output_file.unlink()

        return False


def main():
    print("=" * 60)
    print("SIXSCONTENT — PHASE 3A")
    print("PEXELS VIDEO TEST")
    print("=" * 60)

    successful = 0

    for index, query in enumerate(SEARCHES, start=1):

        video = search_pexels(query)

        if not video:
            continue

        print(f"✅ Found Pexels video ID: {video.get('id')}")
        print(f"🔗 Page: {video.get('url')}")

        if download_video(video, index):
            successful += 1

    print("\n" + "=" * 60)
    print("PHASE 3A RESULT")
    print("=" * 60)

    print(f"Downloaded: {successful}/{len(SEARCHES)} clips")

    if successful == len(SEARCHES):
        print("🔥 PHASE 3A SUCCESS!")
        print("Pexels search and video downloads are working.")
    else:
        print("⚠️ Phase 3A needs attention.")

    print("=" * 60)


if __name__ == "__main__":
    main()
