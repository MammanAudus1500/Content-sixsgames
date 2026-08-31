import os
import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


# ============================================================
# SIXSCONTENT — PHASE 3F
# FINAL CONTENT PACKAGE
# ============================================================

print("=" * 60)
print("🎬 SIXSCONTENT — PHASE 3F")
print("FINAL CONTENT PACKAGE")
print("=" * 60)

print("🚫 Telegram disabled.")
print("🚫 Gemini disabled.")
print("🚫 LTX disabled.")
print("🚫 Automatic publishing disabled.")
print("💰 Target cost: $0")
print("⏱️ GitHub runs only when manually started.")
print()


# ============================================================
# DIRECTORIES
# ============================================================

INPUT_DIR = Path("phase3f_input")
OUTPUT_DIR = Path("phase3f_output")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# FIND PHASE 3E VIDEO
# ============================================================

print("🔎 Searching for Phase 3E final video...")

possible_videos = [
    INPUT_DIR / "phase3e_output" / "sixscontent_phase3e_final.mp4",
    INPUT_DIR / "sixscontent_phase3e_final.mp4",
]

video_path = None

for path in possible_videos:
    if path.exists():
        video_path = path
        break


if video_path is None:
    found = list(INPUT_DIR.rglob("sixscontent_phase3e_final.mp4"))

    if found:
        video_path = found[0]


if video_path is None:
    raise RuntimeError(
        "Phase 3E final video was not found."
    )


print(f"✅ Phase 3E video found:")
print(f"   {video_path}")
print(f"   Size: {video_path.stat().st_size:,} bytes")
print()


# ============================================================
# COPY FINAL VIDEO
# ============================================================

final_video = OUTPUT_DIR / "sixscontent_final.mp4"

shutil.copy2(video_path, final_video)

print("📦 Copying final video...")
print(f"✅ {final_video}")
print()


# ============================================================
# FIND CAPTIONS
# ============================================================

print("🔎 Searching for captions...")

caption_candidates = list(
    INPUT_DIR.rglob("captions.srt")
)

caption_output = OUTPUT_DIR / "captions.srt"

if caption_candidates:
    shutil.copy2(
        caption_candidates[0],
        caption_output
    )

    print(
        f"✅ Captions copied: {caption_output}"
    )
else:
    print(
        "⚠️ captions.srt was not found."
    )

print()


# ============================================================
# FFPROBE
# ============================================================

print("🔍 Inspecting final video...")

probe_command = [
    "ffprobe",
    "-v",
    "error",
    "-show_entries",
    "format=duration,size",
    "-show_entries",
    "stream=width,height,codec_name,codec_type,r_frame_rate",
    "-of",
    "json",
    str(final_video),
]

probe_result = subprocess.run(
    probe_command,
    capture_output=True,
    text=True,
    check=True
)

probe = json.loads(probe_result.stdout)

duration = float(
    probe.get("format", {}).get("duration", 0)
)

size = int(
    probe.get("format", {}).get("size", 0)
)

video_stream = None
audio_stream = None

for stream in probe.get("streams", []):
    if stream.get("codec_type") == "video":
        video_stream = stream

    if stream.get("codec_type") == "audio":
        audio_stream = stream


if video_stream is None:
    raise RuntimeError(
        "Final video contains no video stream."
    )


width = video_stream.get("width")
height = video_stream.get("height")

video_codec = video_stream.get("codec_name")

print(f"   Duration: {duration:.2f}s")
print(f"   Resolution: {width} x {height}")
print(f"   Video codec: {video_codec}")
print(f"   Audio present: {'YES' if audio_stream else 'NO'}")
print()


# ============================================================
# VALIDATION
# ============================================================

print("🧪 Running final validation...")

errors = []

if width != 1080:
    errors.append(
        f"Expected width 1080, got {width}"
    )

if height != 1920:
    errors.append(
        f"Expected height 1920, got {height}"
    )

if duration < 1:
    errors.append(
        "Video duration is too short."
    )

if video_codec != "h264":
    errors.append(
        f"Expected H.264 video, got {video_codec}"
    )

if audio_stream is None:
    errors.append(
        "Final video has no audio stream."
    )


if errors:
    print("❌ Validation failed:")

    for error in errors:
        print(f"   • {error}")

    raise RuntimeError(
        "Phase 3F validation failed."
    )


print("✅ Resolution: 1080 × 1920")
print("✅ Orientation: 9:16")
print("✅ H.264 video")
print("✅ Audio stream present")
print("✅ Valid duration")
print()


# ============================================================
# THUMBNAIL
# ============================================================

print("🖼️ Creating thumbnail...")

thumbnail_path = OUTPUT_DIR / "thumbnail.jpg"

thumbnail_width = 1080
thumbnail_height = 1920

thumbnail = Image.new(
    "RGB",
    (thumbnail_width, thumbnail_height),
    "black"
)

draw = ImageDraw.Draw(thumbnail)


# Try to capture a frame from the video
frame_path = OUTPUT_DIR / "_thumbnail_frame.jpg"

frame_command = [
    "ffmpeg",
    "-y",
    "-ss",
    "3",
    "-i",
    str(final_video),
    "-frames:v",
    "1",
    "-q:v",
    "2",
    str(frame_path),
]

frame_result = subprocess.run(
    frame_command,
    capture_output=True,
    text=True
)

if frame_path.exists():

    try:
        frame = Image.open(frame_path).convert("RGB")

        frame.thumbnail(
            (thumbnail_width, thumbnail_height)
        )

        x = (
            thumbnail_width - frame.width
        ) // 2

        y = (
            thumbnail_height - frame.height
        ) // 2

        thumbnail.paste(
            frame,
            (x, y)
        )

    except Exception as exc:
        print(
            f"⚠️ Could not use video frame: {exc}"
        )


# Dark overlay
overlay = Image.new(
    "RGBA",
    thumbnail.size,
    (0, 0, 0, 80)
)

thumbnail = Image.alpha_composite(
    thumbnail.convert("RGBA"),
    overlay
).convert("RGB")

draw = ImageDraw.Draw(thumbnail)


# Fonts
font_paths = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]

bold_font_path = font_paths[0]
normal_font_path = font_paths[1]

try:
    title_font = ImageFont.truetype(
        bold_font_path,
        92
    )

    subtitle_font = ImageFont.truetype(
        normal_font_path,
        48
    )

except Exception:
    title_font = ImageFont.load_default()
    subtitle_font = ImageFont.load_default()


title = "THE PRICE\nTRICK YOU MISS"

subtitle = "SixsContent"

# Center title
bbox = draw.multiline_textbbox(
    (0, 0),
    title,
    font=title_font,
    spacing=12,
    align="center"
)

text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]

title_x = (
    thumbnail_width - text_width
) // 2

title_y = (
    thumbnail_height - text_height
) // 2 - 100

draw.multiline_text(
    (title_x, title_y),
    title,
    font=title_font,
    fill="white",
    spacing=12,
    align="center",
    stroke_width=3,
    stroke_fill="black"
)


bbox2 = draw.textbbox(
    (0, 0),
    subtitle,
    font=subtitle_font
)

subtitle_width = bbox2[2] - bbox2[0]

draw.text(
    (
        (thumbnail_width - subtitle_width) // 2,
        title_y + text_height + 60
    ),
    subtitle,
    font=subtitle_font,
    fill="white",
    stroke_width=2,
    stroke_fill="black"
)


thumbnail.save(
    thumbnail_path,
    "JPEG",
    quality=92,
    optimize=True
)

print(
    f"✅ Thumbnail created: {thumbnail_path}"
)
print()


# Remove temporary frame
if frame_path.exists():
    frame_path.unlink()


# ============================================================
# CONTENT METADATA
# ============================================================

print("📝 Creating content metadata...")


title = (
    "The Pricing Trick That Makes You Spend More"
)

description = """Have you ever wondered why businesses offer small, medium and large options?

There is a simple pricing strategy behind it.

Once you understand how price anchoring and comparison affect your decisions, you start seeing it everywhere.

Follow SixsContent for more simple business and money insights.
"""

hashtags = [
    "#business",
    "#money",
    "#finance",
    "#businessfacts",
    "#marketing",
    "#pricing",
    "#entrepreneur",
    "#sixscontent",
]


metadata = {
    "brand": "SixsContent",
    "phase": "3F",
    "status": "ready_for_manual_publishing",
    "title": title,
    "description": description,
    "hashtags": hashtags,
    "video": {
        "filename": "sixscontent_final.mp4",
        "format": "MP4",
        "codec": video_codec,
        "width": width,
        "height": height,
        "orientation": "9:16",
        "duration_seconds": round(duration, 2),
        "size_bytes": size,
    },
    "files": {
        "video": "sixscontent_final.mp4",
        "thumbnail": "thumbnail.jpg",
        "captions": (
            "captions.srt"
            if caption_output.exists()
            else None
        ),
    },
    "publishing": {
        "tiktok": False,
        "youtube_shorts": False,
        "instagram_reels": False,
        "telegram": False,
        "automatic_upload": False,
    },
}


metadata_path = (
    OUTPUT_DIR / "content_metadata.json"
)

with open(
    metadata_path,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        metadata,
        file,
        indent=2,
        ensure_ascii=False
    )


print(
    f"✅ Metadata created: {metadata_path}"
)
print()


# ============================================================
# UPLOAD TEXT FILE
# ============================================================

upload_text = OUTPUT_DIR / "upload_text.txt"

with open(
    upload_text,
    "w",
    encoding="utf-8"
) as file:

    file.write(
        "TITLE\n"
        "=====\n"
        f"{title}\n\n"
        "DESCRIPTION\n"
        "===========\n"
        f"{description}\n\n"
        "HASHTAGS\n"
        "========\n"
        f"{' '.join(hashtags)}\n"
    )


print(
    f"✅ Upload text created: {upload_text}"
)
print()


# ============================================================
# CONTENT MANIFEST
# ============================================================

print("📋 Creating package manifest...")

manifest = {
    "project": "SixsContent",
    "phase": "3F",
    "package": "final-content-package",
    "files": [],
}

for path in sorted(OUTPUT_DIR.iterdir()):

    if path.is_file():

        manifest["files"].append(
            {
                "filename": path.name,
                "size_bytes": path.stat().st_size,
            }
        )


manifest_path = (
    OUTPUT_DIR / "manifest.json"
)

with open(
    manifest_path,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        manifest,
        file,
        indent=2
    )


print(
    f"✅ Manifest created: {manifest_path}"
)
print()


# ============================================================
# FINAL SUMMARY
# ============================================================

print("=" * 60)
print("PHASE 3F RESULT")
print("=" * 60)

print("✅ Phase 3E video received")
print("✅ Final video copied")
print("✅ Video validated")
print("✅ 1080 × 1920")
print("✅ 9:16 vertical")
print("✅ H.264")
print("✅ Audio verified")

if caption_output.exists():
    print("✅ Captions included")
else:
    print("⚠️ Captions not included")

print("✅ Thumbnail created")
print("✅ Title created")
print("✅ Description created")
print("✅ Hashtags created")
print("✅ Metadata JSON created")
print("✅ Upload text created")
print("✅ Manifest created")

print()
print("📁 FINAL PACKAGE:")

for path in sorted(OUTPUT_DIR.iterdir()):

    if path.is_file():

        print(
            f"   • {path.name} "
            f"— {path.stat().st_size:,} bytes"
        )

print()
print("🔥 PHASE 3F SUCCESS!")
print("🚀 Content is ready for the publishing phase.")
print("=" * 60)
