import os
import sys
import json
import shutil
import subprocess
from pathlib import Path

print("=" * 60)
print("🎬 SIXSCONTENT — PHASE 3F")
print("FINAL CONTENT PACKAGE")
print("=" * 60)

INPUT = Path("phase3f_input/sixscontent_phase3e_final.mp4")
OUTPUT_DIR = Path("phase3f_output")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

if not INPUT.exists():
    print("❌ Phase 3E final video is missing.")
    print(f"   Expected: {INPUT}")
    sys.exit(1)

print("✅ Phase 3E final video found.")
print(f"💾 Size: {INPUT.stat().st_size:,} bytes")


def run(command):
    print("▶️", " ".join(command))

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    print(result.stdout)

    if result.returncode != 0:
        print(f"❌ Command failed with exit code {result.returncode}")
        sys.exit(result.returncode)


def ffprobe_value(args):
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            *args,
            str(INPUT)
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    return result.stdout.strip()


print("🔧 Checking FFmpeg...")

if shutil.which("ffmpeg") is None:
    print("❌ FFmpeg not available.")
    sys.exit(1)

if shutil.which("ffprobe") is None:
    print("❌ FFprobe not available.")
    sys.exit(1)

print("✅ FFmpeg available.")
print("✅ FFprobe available.")

print("=" * 60)
print("🔍 ANALYZING INPUT VIDEO")
print("=" * 60)

duration = ffprobe_value([
    "-show_entries",
    "format=duration",
    "-of",
    "default=noprint_wrappers=1:nokey=1"
])

width = ffprobe_value([
    "-select_streams",
    "v:0",
    "-show_entries",
    "stream=width",
    "-of",
    "default=noprint_wrappers=1:nokey=1"
])

height = ffprobe_value([
    "-select_streams",
    "v:0",
    "-show_entries",
    "stream=height",
    "-of",
    "default=noprint_wrappers=1:nokey=1"
])

video_codec = ffprobe_value([
    "-select_streams",
    "v:0",
    "-show_entries",
    "stream=codec_name",
    "-of",
    "default=noprint_wrappers=1:nokey=1"
])

audio_codec = ffprobe_value([
    "-select_streams",
    "a:0",
    "-show_entries",
    "stream=codec_name",
    "-of",
    "default=noprint_wrappers=1:nokey=1"
])

print(f"⏱️ Duration: {duration}s")
print(f"📐 Resolution: {width} × {height}")
print(f"🎥 Video codec: {video_codec}")
print(f"🔊 Audio codec: {audio_codec}")

if not width or not height:
    print("❌ Could not determine video dimensions.")
    sys.exit(1)

if int(width) != 1080 or int(height) != 1920:
    print("⚠️ Input is not 1080×1920.")
    print("ℹ️ Phase 3F will normalize the output.")

print("=" * 60)
print("📦 BUILDING FINAL CONTENT PACKAGE")
print("=" * 60)

FINAL_VIDEO = OUTPUT_DIR / "sixscontent_final.mp4"

print("🎬 Creating normalized final MP4...")

run([
    "ffmpeg",
    "-y",
    "-i",
    str(INPUT),

    # Ensure correct vertical format.
    "-vf",
    "scale=1080:1920:force_original_aspect_ratio=decrease,"
    "pad=1080:1920:(ow-iw)/2:(oh-ih)/2",

    "-c:v",
    "libx264",
    "-preset",
    "medium",
    "-crf",
    "23",

    "-c:a",
    "aac",
    "-b:a",
    "128k",

    "-movflags",
    "+faststart",

    str(FINAL_VIDEO)
])

if not FINAL_VIDEO.exists():
    print("❌ Final video was not created.")
    sys.exit(1)

print("✅ Final video created.")
print(f"📁 {FINAL_VIDEO}")
print(f"💾 Size: {FINAL_VIDEO.stat().st_size:,} bytes")

print("=" * 60)
print("📋 CREATING CONTENT METADATA")
print("=" * 60)

metadata = {
    "project": "SixsContent",
    "phase": "3F",
    "status": "ready",
    "video": "sixscontent_final.mp4",
    "format": "MP4",
    "resolution": "1080x1920",
    "orientation": "9:16",
    "source_phase": "3E",
    "voice_over": True,
    "captions": True,
    "pexels_media": True,
    "cost_target": "$0",
    "created_by": "SixsContent automated pipeline"
}

metadata_file = OUTPUT_DIR / "content_metadata.json"

metadata_file.write_text(
    json.dumps(metadata, indent=2),
    encoding="utf-8"
)

print(f"✅ Metadata created: {metadata_file}")

print("=" * 60)
print("📝 CREATING PUBLISHING INFORMATION")
print("=" * 60)

publishing = """SIXSCONTENT — FINAL VIDEO

Video:
sixscontent_final.mp4

Format:
MP4

Resolution:
1080 × 1920

Orientation:
9:16 vertical

Source:
Phase 3E

Includes:
- Pexels visual footage
- Voice-over
- Burned-in captions
- Final normalized video

Status:
READY FOR PUBLISHING

Recommended destinations:
- TikTok
- Instagram Reels
- YouTube Shorts
- Facebook Reels

The file is generated for manual publishing.
No automatic social-media posting is performed in Phase 3F.
"""

publishing_file = OUTPUT_DIR / "publishing_info.txt"

publishing_file.write_text(
    publishing,
    encoding="utf-8"
)

print(f"✅ Publishing information created: {publishing_file}")

print("=" * 60)
print("🔍 FINAL VALIDATION")
print("=" * 60)

if FINAL_VIDEO.stat().st_size <= 0:
    print("❌ Final video is empty.")
    sys.exit(1)

final_duration = subprocess.run(
    [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(FINAL_VIDEO)
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
).stdout.strip()

print(f"⏱️ Final duration: {final_duration}s")
print(f"💾 Final size: {FINAL_VIDEO.stat().st_size:,} bytes")

print("=" * 60)
print("PHASE 3F RESULT")
print("=" * 60)

print("✅ Phase 3E artifact downloaded")
print("✅ Phase 3E video located")
print("✅ Final MP4 normalized")
print("✅ 1080 × 1920 vertical output")
print("✅ Metadata created")
print("✅ Publishing information created")
print("✅ Final package ready")

print("=" * 60)
print("🔥 PHASE 3F SUCCESS!")
print("=" * 60)
