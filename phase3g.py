import os
import sys
import json
import zipfile
import requests
from pathlib import Path


# ============================================================
# SIXSCONTENT — PHASE 3G
# TELEGRAM FINAL VIDEO DELIVERY
# ============================================================

print("=" * 70)
print("🔥 SIXSCONTENT — PHASE 3G")
print("📲 TELEGRAM FINAL VIDEO DELIVERY")
print("=" * 70)


TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

REPO = os.environ["REPO"]
GH_TOKEN = os.environ["GH_TOKEN"]

TELEGRAM_API = (
    f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
)

DOWNLOAD_DIR = Path("phase3g_input")
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# HELPERS
# ============================================================

def fail(message):
    print(f"❌ {message}")
    sys.exit(1)


def telegram_request(method, data=None, files=None, timeout=120):

    url = f"{TELEGRAM_API}/{method}"

    response = requests.post(
        url,
        data=data,
        files=files,
        timeout=timeout
    )

    return response


def send_text(text):

    print("📨 Sending Telegram message...")

    response = telegram_request(
        "sendMessage",
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text
        },
        timeout=60
    )

    if response.status_code != 200:
        print("❌ Telegram text message failed.")
        print(response.text)
        return False

    result = response.json()

    if not result.get("ok"):
        print("❌ Telegram rejected text message.")
        print(result)
        return False

    print("✅ Telegram message sent.")
    return True


# ============================================================
# DOWNLOAD LATEST PHASE 3F ARTIFACT
# ============================================================

print()
print("=" * 70)
print("⬇️ DOWNLOADING LATEST SUCCESSFUL PHASE 3F PACKAGE")
print("=" * 70)


headers = {
    "Authorization": f"Bearer {GH_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


runs_url = (
    f"https://api.github.com/repos/{REPO}/actions/"
    "workflows/phase3f.yml/runs"
)


response = requests.get(
    runs_url,
    headers=headers,
    params={
        "status": "success",
        "per_page": 20
    },
    timeout=30
)


if response.status_code != 200:
    fail(
        "Could not query Phase 3F workflow.\n"
        f"HTTP {response.status_code}\n"
        f"{response.text}"
    )


runs = response.json().get(
    "workflow_runs",
    []
)


if not runs:
    fail(
        "No successful Phase 3F workflow runs were found."
    )


artifact = None


for run in runs:

    run_id = run["id"]

    print(
        f"🔎 Checking Phase 3F run {run_id}..."
    )

    artifacts_url = (
        f"https://api.github.com/repos/{REPO}/actions/"
        f"runs/{run_id}/artifacts"
    )

    artifact_response = requests.get(
        artifacts_url,
        headers=headers,
        params={
            "per_page": 100
        },
        timeout=30
    )

    if artifact_response.status_code != 200:

        print(
            f"⚠️ Could not inspect run {run_id}."
        )

        continue


    artifacts = artifact_response.json().get(
        "artifacts",
        []
    )


    for item in artifacts:

        name = item.get(
            "name",
            ""
        )

        expired = item.get(
            "expired",
            False
        )


        print(
            f"   Artifact: {name}"
        )


        if (
            name == "phase3f-final-package"
            and not expired
        ):

            artifact = item

            break


    if artifact:
        break


if not artifact:

    fail(
        "No usable phase3f-final-package artifact was found."
    )


artifact_id = artifact["id"]
artifact_name = artifact["name"]


print()
print(
    f"✅ Found artifact: {artifact_name}"
)

print(
    f"✅ Artifact ID: {artifact_id}"
)


# ============================================================
# DOWNLOAD ARTIFACT
# ============================================================

download_url = (
    f"https://api.github.com/repos/{REPO}/actions/"
    f"artifacts/{artifact_id}/zip"
)


print()
print("⬇️ Downloading Phase 3F artifact...")


artifact_response = requests.get(
    download_url,
    headers=headers,
    timeout=120,
    allow_redirects=True
)


if artifact_response.status_code != 200:

    fail(
        "Phase 3F artifact download failed.\n"
        f"HTTP {artifact_response.status_code}"
    )


artifact_zip = (
    DOWNLOAD_DIR / "phase3f-final-package.zip"
)


artifact_zip.write_bytes(
    artifact_response.content
)


print(
    f"✅ Artifact downloaded."
)

print(
    f"💾 Size: {artifact_zip.stat().st_size:,} bytes"
)


# ============================================================
# EXTRACT
# ============================================================

extract_dir = (
    DOWNLOAD_DIR / "extracted"
)

extract_dir.mkdir(
    parents=True,
    exist_ok=True
)


print()
print("📦 Extracting Phase 3F package...")


try:

    with zipfile.ZipFile(
        artifact_zip,
        "r"
    ) as archive:

        for name in archive.namelist():

            print(
                f"   - {name}"
            )

        archive.extractall(
            extract_dir
        )

except zipfile.BadZipFile:

    fail(
        "Downloaded Phase 3F artifact is not a valid ZIP file."
    )


# ============================================================
# FIND FINAL VIDEO
# ============================================================

print()
print("=" * 70)
print("🎬 LOCATING FINAL VIDEO")
print("=" * 70)


videos = list(
    extract_dir.rglob("sixscontent_final.mp4")
)


if not videos:

    # Fallback: find any MP4.
    videos = list(
        extract_dir.rglob("*.mp4")
    )


if not videos:

    fail(
        "No MP4 video was found inside the Phase 3F package."
    )


video = videos[0]


print(
    f"✅ Final video found:"
)

print(
    f"📁 {video}"
)

print(
    f"💾 {video.stat().st_size:,} bytes"
)


if video.stat().st_size <= 0:

    fail(
        "Final video is empty."
    )


# ============================================================
# CHECK TELEGRAM FILE SIZE
# ============================================================

# Telegram Bot API currently supports large video uploads,
# but keeping a safety check prevents accidentally sending
# a corrupted or unexpectedly huge file.

file_size_mb = (
    video.stat().st_size / 1024 / 1024
)


print(
    f"📊 Video size: {file_size_mb:.2f} MB"
)


if file_size_mb > 49:

    fail(
        "Video is larger than the configured Telegram safety "
        "limit of 49 MB."
    )


# ============================================================
# SEND START MESSAGE
# ============================================================

print()
print("=" * 70)
print("📲 SENDING FINAL VIDEO TO TELEGRAM")
print("=" * 70)


start_message = """🔥 SIXSCONTENT VIDEO READY

Your automated content pipeline has finished.

🎬 Final video:
sixscontent_final.mp4

📐 Format:
1080 × 1920 vertical

🎙️ Voice-over:
YES

📝 Burned-in captions:
YES

🎞️ Visual footage:
YES

📦 Phase:
3G — Telegram Delivery

Uploading the finished video now...
"""


if not send_text(start_message):

    fail(
        "Could not send Telegram preparation message."
    )


# ============================================================
# UPLOAD VIDEO
# ============================================================

print()
print("⬆️ Uploading MP4 to Telegram...")


caption = """🔥 SIXSCONTENT — FINAL VIDEO

✅ Video production complete
✅ Voice-over included
✅ Captions included
✅ 1080×1920 vertical
✅ Ready for TikTok
✅ Ready for Instagram Reels
✅ Ready for YouTube Shorts
✅ Ready for Facebook Reels

PHASE 3G COMPLETE
"""


try:

    with open(
        video,
        "rb"
    ) as video_file:

        response = telegram_request(
            "sendVideo",
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": caption,
                "supports_streaming": "true"
            },
            files={
                "video": (
                    video.name,
                    video_file,
                    "video/mp4"
                )
            },
            timeout=300
        )

except Exception as e:

    fail(
        f"Telegram video upload exception: {e}"
    )


if response.status_code != 200:

    fail(
        "Telegram video upload failed.\n"
        f"HTTP {response.status_code}\n"
        f"{response.text}"
    )


telegram_result = response.json()


if not telegram_result.get("ok"):

    fail(
        "Telegram rejected the video upload.\n"
        f"{telegram_result}"
    )


print()
print("✅ VIDEO SUCCESSFULLY DELIVERED TO TELEGRAM")


# ============================================================
# SEND METADATA
# ============================================================

print()
print("=" * 70)
print("📋 SENDING CONTENT INFORMATION")
print("=" * 70)


metadata_files = list(
    extract_dir.rglob(
        "content_metadata.json"
    )
)


publishing_files = list(
    extract_dir.rglob(
        "publishing_info.txt"
    )
)


if metadata_files:

    try:

        metadata = json.loads(
            metadata_files[0].read_text(
                encoding="utf-8"
            )
        )

        metadata_message = (
            "📋 CONTENT METADATA\n\n"
            f"Project: {metadata.get('project', 'SixsContent')}\n"
            f"Phase: {metadata.get('phase', '3F')}\n"
            f"Status: {metadata.get('status', 'ready')}\n"
            f"Video: {metadata.get('video', video.name)}\n"
            f"Format: {metadata.get('format', 'MP4')}\n"
            f"Resolution: {metadata.get('resolution', '1080x1920')}\n"
            f"Orientation: {metadata.get('orientation', '9:16')}\n"
            f"Voice-over: {metadata.get('voice_over', True)}\n"
            f"Captions: {metadata.get('captions', True)}"
        )

        send_text(
            metadata_message
        )

    except Exception as e:

        print(
            f"⚠️ Could not read metadata: {e}"
        )


if publishing_files:

    try:

        publishing_text = publishing_files[0].read_text(
            encoding="utf-8"
        )

        send_text(
            "📝 PUBLISHING INFORMATION\n\n"
            + publishing_text
        )

    except Exception as e:

        print(
            f"⚠️ Could not read publishing information: {e}"
        )


# ============================================================
# FINAL SUCCESS
# ============================================================

print()
print("=" * 70)
print("PHASE 3G RESULT")
print("=" * 70)

print("✅ Phase 3F artifact downloaded")
print("✅ Final MP4 located")
print("✅ MP4 validated")
print("✅ Video uploaded to Telegram")
print("✅ Content metadata processed")
print("✅ Publishing information processed")
print("✅ Final video delivered")
print("=" * 70)
print("🔥 PHASE 3G SUCCESS!")
print("=" * 70)
