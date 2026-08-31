import os
import sys
import requests
from pathlib import Path

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

OUTPUT_DIR = Path("phase3c_videos")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

VIDEO_QUERIES = [
    "money business finance",
    "business meeting",
    "person using smartphone",
    "technology laptop",
    "success entrepreneur",
]

MAX_VIDEOS = 5


def fail(message):
    print("")
    print("❌ ERROR")
    print(message)
    print("")
    sys.exit(1)


def search_pexels_video(query):
    print(f"🔎 Searching Pexels videos: {query}")

    url = "https://api.pexels.com/videos/search"

    headers = {
        "Authorization": PEXELS_API_KEY
    }

    params = {
        "query": query,
        "orientation": "portrait",
        "size": "medium",
        "per_page": 5
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=30
    )

    print(f"   HTTP status: {response.status_code}")

    if response.status_code != 200:
        print(response.text[:1000])
        return []

    data = response.json()

    videos = data.get("videos", [])

    print(f"   Found {len(videos)} videos.")

    return videos


def choose_video_file(video):
    files = video.get("video_files", [])

    if not files:
        return None

    # Prefer portrait/vertical files.
    portrait_files = [
        f for f in files
        if f.get("width", 0) < f.get("height", 0)
    ]

    candidates = portrait_files if portrait_files else files

    # Prefer reasonable resolution.
    candidates = sorted(
        candidates,
        key=lambda x: (
            abs(x.get("width", 0) - 1080),
            abs(x.get("height", 0) - 1920)
        )
    )

    return candidates[0] if candidates else None


def download_video(video_file, output_path):
    video_url = video_file.get("link")

    if not video_url:
        return False

    print(f"⬇️ Downloading {output_path.name}...")

    try:
        with requests.get(
            video_url,
            stream=True,
            timeout=120
        ) as response:

            if response.status_code != 200:
                print(
                    f"   ❌ Download failed: "
                    f"HTTP {response.status_code}"
                )
                return False

            with open(output_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        file.write(chunk)

        size = output_path.stat().st_size

        print(
            f"   ✅ Saved {output_path} "
            f"({size:,} bytes)"
        )

        return True

    except Exception as error:
        print(f"   ❌ Download error: {error}")
        return False


def main():

    print("=" * 60)
    print("🎬 SIXSCONTENT — PHASE 3C")
    print("PEXELS VIDEO COLLECTION TEST")
    print("=" * 60)

    if not PEXELS_API_KEY:
        fail(
            "PEXELS_API_KEY is missing.\n"
            "Add it to GitHub Actions Secrets."
        )

    print("✅ Pexels API key detected.")
    print("🚫 Gemini disabled in Phase 3C.")
    print("🚫 Telegram disabled in Phase 3C.")
    print("🚫 LTX disabled in Phase 3C.")
    print("🎥 Testing REAL Pexels video footage.")

    downloaded = 0
    used_video_ids = set()

    for query in VIDEO_QUERIES:

        if downloaded >= MAX_VIDEOS:
            break

        videos = search_pexels_video(query)

        for video in videos:

            if downloaded >= MAX_VIDEOS:
                break

            video_id = video.get("id")

            if video_id in used_video_ids:
                continue

            video_file = choose_video_file(video)

            if not video_file:
                continue

            width = video_file.get("width", 0)
            height = video_file.get("height", 0)

            print(
                f"   Selected video {video_id}: "
                f"{width}x{height}"
            )

            output_path = (
                OUTPUT_DIR /
                f"clip_{downloaded + 1:02d}.mp4"
            )

            success = download_video(
                video_file,
                output_path
            )

            if success:
                used_video_ids.add(video_id)
                downloaded += 1

    print("")
    print("=" * 60)
    print("PHASE 3C RESULT")
    print("=" * 60)

    print(f"✅ Videos downloaded: {downloaded}")
    print(f"📁 Folder: {OUTPUT_DIR}")

    if downloaded == 0:
        fail(
            "No Pexels videos were downloaded."
        )

    print("")
    print("🔥 PHASE 3C SUCCESS!")
    print("")
    print("Files:")

    for file in sorted(OUTPUT_DIR.glob("*.mp4")):
        size = file.stat().st_size
        print(
            f"  • {file.name} — {size:,} bytes"
        )

    print("")
    print("GitHub will now stop automatically.")
    print("No 24/7 process is running.")


if __name__ == "__main__":
    main()
