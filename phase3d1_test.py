import os
import sys
import subprocess
import requests
from pathlib import Path

PEXELS_API_KEY = os.environ["PEXELS_API_KEY"]

OUTPUT_DIR = Path("phase3d1_videos")
OUTPUT_DIR.mkdir(exist_ok=True)

FINAL_VIDEO = Path("sixscontent_phase3d1.mp4")

SEARCH_QUERY = "money business finance"

print("=" * 60)
print("🎬 SIXSCONTENT — PHASE 3D-1")
print("PEXELS → FFMPEG → ONE FINISHED VIDEO")
print("=" * 60)

print("✅ Pexels API key detected.")
print("🚫 Gemini disabled.")
print("🚫 Telegram disabled.")
print("🚫 LTX disabled.")

# ---------------------------------------------------------
# Check FFmpeg
# ---------------------------------------------------------

print("\n🔧 Checking FFmpeg...")

try:
    result = subprocess.run(
        ["ffmpeg", "-version"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError("FFmpeg check failed.")

    print("✅ FFmpeg is available.")

except Exception as e:
    print("❌ FFmpeg is not available.")
    print(str(e))
    sys.exit(1)


# ---------------------------------------------------------
# Search Pexels videos
# ---------------------------------------------------------

print(f"\n🔎 Searching Pexels videos: {SEARCH_QUERY}")

headers = {
    "Authorization": PEXELS_API_KEY
}

params = {
    "query": SEARCH_QUERY,
    "per_page": 10,
    "orientation": "portrait"
}

response = requests.get(
    "https://api.pexels.com/videos/search",
    headers=headers,
    params=params,
    timeout=30
)

print(f"   HTTP status: {response.status_code}")

if response.status_code != 200:
    print("❌ Pexels API request failed.")
    print(response.text)
    sys.exit(1)

data = response.json()

videos = data.get("videos", [])

if len(videos) < 5:
    print(f"❌ Only found {len(videos)} videos.")
    print("Need at least 5 videos.")
    sys.exit(1)

print(f"   Found {len(videos)} videos.")


# ---------------------------------------------------------
# Download 5 videos
# ---------------------------------------------------------

downloaded = []

for index, video in enumerate(videos[:5], start=1):

    video_id = video.get("id")

    files = video.get("video_files", [])

    if not files:
        print(f"⚠️ Video {video_id} has no downloadable files.")
        continue

    # Prefer portrait HD files.
    candidates = []

    for file in files:
        width = file.get("width") or 0
        height = file.get("height") or 0
        link = file.get("link")

        if not link:
            continue

        if height >= width:
            candidates.append(file)

    if not candidates:
        candidates = files

    # Prefer 1080p-ish footage without going unnecessarily huge.
    candidates.sort(
        key=lambda x: (
            abs((x.get("width") or 0) - 1080),
            -(x.get("height") or 0)
        )
    )

    selected = candidates[0]

    download_url = selected["link"]

    output_file = OUTPUT_DIR / f"clip_{index:02d}.mp4"

    print(
        f"\n⬇️ Downloading clip {index} "
        f"(Pexels ID {video_id})..."
    )

    try:
        with requests.get(
            download_url,
            stream=True,
            timeout=120
        ) as r:

            r.raise_for_status()

            with open(output_file, "wb") as f:

                for chunk in r.iter_content(chunk_size=1024 * 1024):

                    if chunk:
                        f.write(chunk)

        size = output_file.stat().st_size

        print(
            f"   ✅ Saved {output_file} "
            f"({size:,} bytes)"
        )

        downloaded.append(output_file)

    except Exception as e:

        print(
            f"   ❌ Download failed for clip {index}: {e}"
        )


if len(downloaded) < 5:

    print(
        f"\n❌ Only downloaded {len(downloaded)} usable videos."
    )

    sys.exit(1)


# ---------------------------------------------------------
# Prepare clips
# ---------------------------------------------------------

print("\n🎞️ Preparing clips for vertical output...")

prepared_files = []

for index, input_file in enumerate(downloaded, start=1):

    output_file = OUTPUT_DIR / f"prepared_{index:02d}.mp4"

    print(
        f"   Processing clip {index}/5..."
    )

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_file),

        # Take first 8 seconds from each clip.
        "-t",
        "8",

        # Vertical 1080x1920 output.
        "-vf",
        (
            "scale=1080:1920:"
            "force_original_aspect_ratio=increase,"
            "crop=1080:1920"
        ),

        "-an",

        "-c:v",
        "libx264",

        "-preset",
        "veryfast",

        "-crf",
        "23",

        "-pix_fmt",
        "yuv420p",

        "-r",
        "30",

        "-movflags",
        "+faststart",

        str(output_file)
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:

        print(
            f"❌ FFmpeg failed on clip {index}"
        )

        print(result.stderr[-3000:])

        sys.exit(1)

    prepared_files.append(output_file)

    print(
        f"   ✅ Prepared {output_file.name}"
    )


# ---------------------------------------------------------
# Create concat list
# ---------------------------------------------------------

concat_file = OUTPUT_DIR / "concat.txt"

with open(concat_file, "w", encoding="utf-8") as f:

    for file in prepared_files:

        absolute_path = file.resolve()

        # FFmpeg concat file syntax.
        safe_path = str(absolute_path).replace("'", "'\\''")

        f.write(
            f"file '{safe_path}'\n"
        )


# ---------------------------------------------------------
# Concatenate
# ---------------------------------------------------------

print("\n🎬 Combining 5 clips into ONE video...")

concat_command = [
    "ffmpeg",
    "-y",

    "-f",
    "concat",

    "-safe",
    "0",

    "-i",
    str(concat_file),

    "-c",
    "copy",

    "-movflags",
    "+faststart",

    str(FINAL_VIDEO)
]

result = subprocess.run(
    concat_command,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

if result.returncode != 0:

    print("❌ FFmpeg concatenation failed.")

    print(result.stderr[-5000:])

    sys.exit(1)


# ---------------------------------------------------------
# Verify final file
# ---------------------------------------------------------

if not FINAL_VIDEO.exists():

    print("❌ Final MP4 was not created.")

    sys.exit(1)

final_size = FINAL_VIDEO.stat().st_size


# ---------------------------------------------------------
# Get video information
# ---------------------------------------------------------

print("\n🔍 Checking final video...")

probe_command = [
    "ffprobe",
    "-v",
    "error",
    "-show_entries",
    "format=duration",
    "-of",
    "default=noprint_wrappers=1:nokey=1",
    str(FINAL_VIDEO)
]

probe = subprocess.run(
    probe_command,
    capture_output=True,
    text=True
)

duration = probe.stdout.strip()

print("=" * 60)
print("PHASE 3D-1 RESULT")
print("=" * 60)

print("✅ Pexels videos downloaded: 5")
print("✅ Clips processed: 5")
print("✅ Clips combined: YES")
print(f"✅ Final video: {FINAL_VIDEO}")
print(f"✅ Final size: {final_size:,} bytes")

if duration:
    print(f"✅ Duration: {duration} seconds")

print("✅ Format: MP4")
print("✅ Target resolution: 1080 × 1920")
print("✅ Target orientation: 9:16")

print("=" * 60)
print("🔥 PHASE 3D-1 SUCCESS!")
print("=" * 60)

print("GitHub will now stop automatically.")
print("No 24/7 process is running.")
