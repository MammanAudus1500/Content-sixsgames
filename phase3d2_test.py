import os
import re
import shutil
import subprocess
from pathlib import Path

import requests


# ============================================================
# SIXSCONTENT — PHASE 3D-2
# GEMINI VISUAL DIRECTIONS → PEXELS → FFMPEG
# ============================================================

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

OUTPUT_DIR = Path("phase3d2_output")
DOWNLOAD_DIR = OUTPUT_DIR / "downloads"
PREPARED_DIR = OUTPUT_DIR / "prepared"

FINAL_VIDEO = OUTPUT_DIR / "sixscontent_phase3d2.mp4"

TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920

# Test content.
# In the final integration, Gemini will provide these automatically.
VISUAL_DIRECTIONS = [
    "movie theater popcorn menu with small medium and large prices",
    "person choosing between small and large popcorn",
    "business pricing strategy and price comparison",
    "shopping customer looking at receipt",
    "subscription pricing plans with three options",
]

CLIP_SECONDS = 8


# ============================================================
# BASIC HELPERS
# ============================================================

def log(message=""):
    print(message, flush=True)


def clean_directory(path):
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def check_ffmpeg():
    log("🔧 Checking FFmpeg...")

    result = subprocess.run(
        ["ffmpeg", "-version"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError("FFmpeg is not available.")

    log("✅ FFmpeg is available.")


# ============================================================
# PEXELS
# ============================================================

def search_pexels_videos(query, per_page=10):
    url = "https://api.pexels.com/v1/videos/search"

    headers = {
        "Authorization": PEXELS_API_KEY
    }

    params = {
        "query": query,
        "orientation": "portrait",
        "per_page": per_page
    }

    log(f"🔎 Pexels search: {query}")

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=30
    )

    log(f"   HTTP status: {response.status_code}")

    response.raise_for_status()

    data = response.json()

    videos = data.get("videos", [])

    log(f"   Found {len(videos)} videos.")

    return videos


def choose_video(videos):
    if not videos:
        return None

    # Prefer vertical videos.
    vertical = []

    for video in videos:
        width = video.get("width", 0)
        height = video.get("height", 0)

        if height > width:
            vertical.append(video)

    if vertical:
        return vertical[0]

    return videos[0]


def choose_download_link(video):
    files = video.get("video_files", [])

    if not files:
        return None

    # Prefer MP4 files.
    mp4_files = [
        item for item in files
        if item.get("file_type") == "video/mp4"
    ]

    if not mp4_files:
        mp4_files = files

    # Prefer the largest usable vertical file.
    vertical = [
        item for item in mp4_files
        if item.get("height", 0) >= item.get("width", 0)
    ]

    candidates = vertical if vertical else mp4_files

    candidates.sort(
        key=lambda item: (
            item.get("width", 0) * item.get("height", 0)
        ),
        reverse=True
    )

    return candidates[0].get("link")


def download_file(url, output_path):
    with requests.get(
        url,
        stream=True,
        timeout=120
    ) as response:

        response.raise_for_status()

        with open(output_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    file.write(chunk)


# ============================================================
# FFMPEG
# ============================================================

def process_clip(input_file, output_file):
    """
    Convert the downloaded clip into:
    1080x1920
    9:16
    H.264 MP4
    Maximum 8 seconds
    """

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_file),

        "-t",
        str(CLIP_SECONDS),

        "-vf",
        (
            "scale=1080:1920:"
            "force_original_aspect_ratio=increase,"
            "crop=1080:1920"
        ),

        "-c:v",
        "libx264",

        "-preset",
        "veryfast",

        "-crf",
        "23",

        "-an",

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
        print(result.stderr)
        raise RuntimeError(
            f"FFmpeg failed for {input_file}"
        )


def combine_clips(files, output_file):
    concat_file = OUTPUT_DIR / "concat.txt"

    with open(concat_file, "w", encoding="utf-8") as f:
        for file in files:
            absolute_path = file.resolve()

            safe_path = str(absolute_path).replace(
                "'",
                "'\\''"
            )

            f.write(
                f"file '{safe_path}'\n"
            )

    command = [
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

        str(output_file)
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError(
            "FFmpeg failed while combining clips."
        )


def get_duration(file):
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(file)
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        return 0

    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0


# ============================================================
# MAIN
# ============================================================

def main():

    log("=" * 60)
    log("🎬 SIXSCONTENT — PHASE 3D-2")
    log("GEMINI VISUAL DIRECTIONS → PEXELS → FFMPEG")
    log("=" * 60)

    if not PEXELS_API_KEY:
        raise RuntimeError(
            "PEXELS_API_KEY secret is missing."
        )

    log("✅ Pexels API key detected.")
    log("🚫 Telegram disabled.")
    log("🚫 LTX disabled.")
    log("🚫 Gemini API call disabled in this test.")
    log("ℹ️ Using Gemini-style visual directions as test input.")

    check_ffmpeg()

    clean_directory(OUTPUT_DIR)
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    PREPARED_DIR.mkdir(parents=True, exist_ok=True)

    processed_clips = []

    # ========================================================
    # SEARCH + DOWNLOAD
    # ========================================================

    for index, visual in enumerate(
        VISUAL_DIRECTIONS,
        start=1
    ):

        log("")
        log(
            f"🎬 SCENE {index}/{len(VISUAL_DIRECTIONS)}"
        )
        log(f"📝 Visual direction: {visual}")

        try:

            videos = search_pexels_videos(
                visual,
                per_page=10
            )

            selected = choose_video(videos)

            if not selected:
                log(
                    "⚠️ No suitable Pexels video found."
                )
                continue

            video_id = selected.get("id")

            log(
                f"   Selected Pexels video: {video_id}"
            )

            log(
                f"   Source dimensions: "
                f"{selected.get('width')}x"
                f"{selected.get('height')}"
            )

            link = choose_download_link(selected)

            if not link:
                log(
                    "⚠️ No downloadable MP4 found."
                )
                continue

            download_path = (
                DOWNLOAD_DIR /
                f"clip_{index:02d}.mp4"
            )

            log(
                f"⬇️ Downloading {download_path.name}..."
            )

            download_file(
                link,
                download_path
            )

            size = download_path.stat().st_size

            log(
                f"   ✅ Downloaded "
                f"({size:,} bytes)"
            )

            prepared_path = (
                PREPARED_DIR /
                f"prepared_{index:02d}.mp4"
            )

            log(
                "🎞️ Converting to 1080x1920..."
            )

            process_clip(
                download_path,
                prepared_path
            )

            duration = get_duration(
                prepared_path
            )

            log(
                f"   ✅ Prepared "
                f"({duration:.2f}s)"
            )

            processed_clips.append(
                prepared_path
            )

        except Exception as error:

            log(
                f"⚠️ Scene {index} failed:"
            )

            log(
                f"   {error}"
            )

    # ========================================================
    # COMBINE
    # ========================================================

    if not processed_clips:
        raise RuntimeError(
            "No clips were successfully processed."
        )

    log("")
    log("=" * 60)
    log("🎬 COMBINING CLIPS")
    log("=" * 60)

    log(
        f"✅ Usable clips: "
        f"{len(processed_clips)}"
    )

    combine_clips(
        processed_clips,
        FINAL_VIDEO
    )

    # ========================================================
    # FINAL CHECK
    # ========================================================

    duration = get_duration(
        FINAL_VIDEO
    )

    size = FINAL_VIDEO.stat().st_size

    log("")
    log("=" * 60)
    log("PHASE 3D-2 RESULT")
    log("=" * 60)

    log(
        f"✅ Scenes requested: "
        f"{len(VISUAL_DIRECTIONS)}"
    )

    log(
        f"✅ Clips processed: "
        f"{len(processed_clips)}"
    )

    log(
        "✅ Pexels footage matched "
        "to individual visual directions"
    )

    log(
        "✅ Clips combined: YES"
    )

    log(
        f"✅ Final video: "
        f"{FINAL_VIDEO}"
    )

    log(
        f"✅ Final size: "
        f"{size:,} bytes"
    )

    log(
        f"✅ Duration: "
        f"{duration:.2f} seconds"
    )

    log(
        "✅ Target format: MP4"
    )

    log(
        "✅ Target resolution: 1080 × 1920"
    )

    log(
        "✅ Target orientation: 9:16"
    )

    log("")
    log("🔥 PHASE 3D-2 SUCCESS!")
    log("")
    log(
        "GitHub will now stop automatically."
    )
    log(
        "No 24/7 process is running."
    )


if __name__ == "__main__":
    main()
