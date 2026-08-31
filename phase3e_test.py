import os
import sys
import json
import zipfile
import shutil
import subprocess
from pathlib import Path

import requests


# ============================================================
# SIXSCONTENT — PHASE 3E
# PEXELS VIDEO + FREE TTS + CAPTIONS
# ============================================================

OUTPUT_DIR = Path("phase3e_output")
INPUT_DIR = Path("phase3e_input")

ARTIFACT_NAME = "phase3d2-video"

VIDEO_NAME = "sixscontent_phase3d2.mp4"


SCRIPT = """
Think about the last time you bought popcorn at the movies.

A small costs four dollars.
A large costs seven.

Seven dollars for popcorn feels like a total rip-off, right?
So you'd probably just stick to the small.

Now, enter the medium popcorn for six dollars and fifty cents.

Suddenly, that seven-dollar large doesn't feel expensive anymore.
It feels like a steal.

For just fifty cents extra, you get the biggest size.

This is a psychological pricing strategy called the Decoy Effect.

The medium size isn't actually designed to sell.

Its sole purpose is to act as bait — a dummy option specifically placed to make the highest price look like an irresistible bargain.

Behavioral economists have tested this exact scenario.

When given only small and large choices, the majority of people stick to the cheaper option.

But as soon as the decoy medium is introduced, the vast majority jump straight to the most expensive choice.

You see this every day:
tech upgrades,
coffee sizes,
streaming subscriptions,
and fast food menus.

Next time you feel like you're getting an unbelievable deal, ask yourself:

Did you actually want the large,
or did you just walk straight into the decoy trap?
""".strip()


def run_command(command):
    print(">", " ".join(str(x) for x in command))

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    print(result.stdout)

    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed with exit code {result.returncode}"
        )


def check_ffmpeg():
    print("🔧 Checking FFmpeg...")

    result = subprocess.run(
        ["ffmpeg", "-version"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    if result.returncode != 0:
        raise RuntimeError("FFmpeg is not available.")

    print("✅ FFmpeg is available.")


def get_github_headers():
    token = os.environ.get("GITHUB_TOKEN")

    if not token:
        raise RuntimeError(
            "GITHUB_TOKEN is missing. "
            "The workflow must provide the GitHub Actions token."
        )

    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def get_repository():
    repository = os.environ.get("GITHUB_REPOSITORY")

    if not repository:
        raise RuntimeError("GITHUB_REPOSITORY is missing.")

    return repository


def download_phase3d2_artifact():
    print("=" * 60)
    print("📦 DOWNLOADING PHASE 3D-2 ARTIFACT")
    print("=" * 60)

    repository = get_repository()
    headers = get_github_headers()

    url = (
        f"https://api.github.com/repos/"
        f"{repository}/actions/artifacts"
    )

    params = {
        "name": ARTIFACT_NAME,
        "per_page": 20,
    }

    print(f"🔎 Searching GitHub artifacts: {ARTIFACT_NAME}")

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=30
    )

    print(f"   HTTP status: {response.status_code}")

    response.raise_for_status()

    data = response.json()

    artifacts = data.get("artifacts", [])

    valid_artifacts = [
        artifact
        for artifact in artifacts
        if artifact.get("name") == ARTIFACT_NAME
        and not artifact.get("expired", False)
    ]

    if not valid_artifacts:
        raise RuntimeError(
            "No usable Phase 3D-2 artifact was found."
        )

    # GitHub returns newest artifacts first in normal usage,
    # but sort explicitly to be safe.
    valid_artifacts.sort(
        key=lambda x: x.get("created_at", ""),
        reverse=True
    )

    artifact = valid_artifacts[0]

    artifact_id = artifact["id"]
    artifact_url = artifact["archive_download_url"]

    print(f"✅ Found artifact ID: {artifact_id}")
    print(f"📅 Created: {artifact.get('created_at')}")
    print("⬇️ Downloading artifact...")

    INPUT_DIR.mkdir(parents=True, exist_ok=True)

    zip_path = INPUT_DIR / "phase3d2_artifact.zip"

    with requests.get(
        artifact_url,
        headers=headers,
        stream=True,
        timeout=120
    ) as download:

        download.raise_for_status()

        total = 0

        with open(zip_path, "wb") as file:
            for chunk in download.iter_content(
                chunk_size=1024 * 1024
            ):
                if chunk:
                    file.write(chunk)
                    total += len(chunk)

    print(
        f"✅ Artifact downloaded: {total:,} bytes"
    )

    extract_dir = INPUT_DIR / "extracted"

    if extract_dir.exists():
        shutil.rmtree(extract_dir)

    extract_dir.mkdir(parents=True)

    print("📂 Extracting artifact...")

    with zipfile.ZipFile(zip_path, "r") as archive:
        archive.extractall(extract_dir)

    print("✅ Artifact extracted.")

    candidates = list(
        extract_dir.rglob(VIDEO_NAME)
    )

    if not candidates:
        print("📋 Files found inside artifact:")

        for path in extract_dir.rglob("*"):
            if path.is_file():
                print(f" - {path}")

        raise RuntimeError(
            f"Could not find {VIDEO_NAME} inside "
            f"the Phase 3D-2 artifact."
        )

    source_video = candidates[0]

    print(
        f"✅ Phase 3D-2 video located: {source_video}"
    )

    return source_video


def prepare_directories():
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)

    OUTPUT_DIR.mkdir(parents=True)

    return OUTPUT_DIR


def create_voiceover():
    print("=" * 60)
    print("🎙️ FREE VOICE-OVER")
    print("=" * 60)

    try:
        import edge_tts
    except ImportError:
        raise RuntimeError(
            "edge-tts is not installed."
        )

    voice = "en-US-ChristopherNeural"

    text_file = OUTPUT_DIR / "script.txt"
    audio_file = OUTPUT_DIR / "voiceover.mp3"

    text_file.write_text(
        SCRIPT,
        encoding="utf-8"
    )

    print(f"🎙️ Voice: {voice}")
    print("🔊 Generating voice-over with Edge TTS...")

    async def generate():
        communicate = edge_tts.Communicate(
            SCRIPT,
            voice
        )

        await communicate.save(
            str(audio_file)
        )

    import asyncio

    asyncio.run(generate())

    if not audio_file.exists():
        raise RuntimeError(
            "Voice-over file was not created."
        )

    size = audio_file.stat().st_size

    print(
        f"✅ Voice-over created: "
        f"{size:,} bytes"
    )

    return audio_file


def create_captions():
    print("=" * 60)
    print("📝 CREATING CAPTIONS")
    print("=" * 60)

    caption_file = OUTPUT_DIR / "captions.srt"

    # Caption timing is intentionally simple and robust.
    # The final video/audio duration is used later.
    sentences = [
        "Think about the last time you bought popcorn at the movies.",
        "A small costs four dollars. A large costs seven.",
        "Seven dollars for popcorn feels like a total rip-off, right?",
        "So you'd probably just stick to the small.",
        "Now, enter the medium popcorn for six dollars and fifty cents.",
        "Suddenly, that seven-dollar large doesn't feel expensive anymore.",
        "It feels like a steal.",
        "For just fifty cents extra, you get the biggest size.",
        "This is a psychological pricing strategy called the Decoy Effect.",
        "The medium size isn't actually designed to sell.",
        "Its sole purpose is to act as bait.",
        "A dummy option specifically placed to make the highest price look like an irresistible bargain.",
        "Behavioral economists have tested this exact scenario.",
        "When given only small and large choices, the majority stick to the cheaper option.",
        "But when the decoy medium is introduced, more people choose the most expensive option.",
        "You see this every day: tech upgrades, coffee sizes, streaming subscriptions, and fast food menus.",
        "Next time you feel like you're getting an unbelievable deal, ask yourself:",
        "Did you actually want the large, or did you just walk straight into the decoy trap?"
    ]

    # Approximately 2.6 seconds per caption.
    start = 0.0
    duration = 2.6

    def srt_time(seconds):
        milliseconds = int(round(seconds * 1000))

        hours = milliseconds // 3600000
        milliseconds %= 3600000

        minutes = milliseconds // 60000
        milliseconds %= 60000

        seconds_value = milliseconds // 1000
        milliseconds %= 1000

        return (
            f"{hours:02d}:"
            f"{minutes:02d}:"
            f"{seconds_value:02d},"
            f"{milliseconds:03d}"
        )

    blocks = []

    for index, sentence in enumerate(sentences, start=1):

        end = start + duration

        blocks.append(
            f"{index}\n"
            f"{srt_time(start)} --> {srt_time(end)}\n"
            f"{sentence}\n"
        )

        start = end

    caption_file.write_text(
        "\n".join(blocks),
        encoding="utf-8"
    )

    print(
        f"✅ Captions created: {caption_file}"
    )

    return caption_file


def combine_video(video, audio, captions):
    print("=" * 60)
    print("🎬 COMBINING VIDEO + VOICE + CAPTIONS")
    print("=" * 60)

    final_video = (
        OUTPUT_DIR /
        "sixscontent_phase3e_final.mp4"
    )

    # Convert caption path to FFmpeg-safe form.
    caption_path = str(
        captions.resolve()
    ).replace("\\", "/")

    # Escape colon for FFmpeg subtitle filter.
    caption_path = caption_path.replace(
        ":",
        "\\:"
    )

    command = [
        "ffmpeg",
        "-y",

        "-i",
        str(video),

        "-i",
        str(audio),

        "-vf",
        (
            f"subtitles='{caption_path}':"
            "force_style="
            "'FontName=Arial,"
            "FontSize=16,"
            "Bold=1,"
            "Alignment=2,"
            "MarginV=120'"
        ),

        "-map",
        "0:v:0",

        "-map",
        "1:a:0",

        "-c:v",
        "libx264",

        "-preset",
        "veryfast",

        "-crf",
        "23",

        "-c:a",
        "aac",

        "-b:a",
        "128k",

        "-shortest",

        "-movflags",
        "+faststart",

        str(final_video),
    ]

    run_command(command)

    if not final_video.exists():
        raise RuntimeError(
            "Final video was not created."
        )

    return final_video


def inspect_video(video):
    print("=" * 60)
    print("🔍 CHECKING FINAL VIDEO")
    print("=" * 60)

    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration,size",
        "-show_entries",
        "stream=width,height,codec_name",
        "-of",
        "json",
        str(video)
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(
            "ffprobe failed."
        )

    data = json.loads(result.stdout)

    duration = data.get(
        "format",
        {}
    ).get(
        "duration",
        "unknown"
    )

    size = video.stat().st_size

    print(f"📁 File: {video}")
    print(f"💾 Size: {size:,} bytes")
    print(f"⏱️ Duration: {duration} seconds")

    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video":
            print(
                f"🎥 Video: "
                f"{stream.get('width')}x"
                f"{stream.get('height')} "
                f"({stream.get('codec_name')})"
            )

        if stream.get("codec_type") == "audio":
            print(
                f"🔊 Audio: "
                f"{stream.get('codec_name')}"
            )


def main():
    print("=" * 60)
    print("🎬 SIXSCONTENT — PHASE 3E")
    print("PEXELS + FREE TTS + CAPTIONS")
    print("=" * 60)

    print("🚫 Gemini disabled.")
    print("🚫 Telegram disabled.")
    print("🚫 LTX disabled.")
    print("💰 Target cost: $0")
    print("⏱️ GitHub runs only when manually started.")

    check_ffmpeg()

    prepare_directories()

    source_video = download_phase3d2_artifact()

    print("=" * 60)
    print("🎙️ VOICE + CAPTIONS")
    print("=" * 60)

    audio = create_voiceover()

    captions = create_captions()

    final_video = combine_video(
        source_video,
        audio,
        captions
    )

    inspect_video(final_video)

    print("=" * 60)
    print("PHASE 3E RESULT")
    print("=" * 60)

    print("✅ Phase 3D-2 artifact downloaded")
    print("✅ Voice-over generated")
    print("✅ Captions generated")
    print("✅ Video + voice combined")
    print("✅ Captions burned into video")
    print(f"✅ Final video: {final_video}")

    print("=" * 60)
    print("🔥 PHASE 3E SUCCESS!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()

    except Exception as error:
        print()
        print("❌ PHASE 3E FAILED")
        print(f"Error: {error}")
        sys.exit(1)
