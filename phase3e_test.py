import os
import subprocess
import sys
import requests
from pathlib import Path

# ============================================================
# SIXSCONTENT — PHASE 3E
# PEXELS VIDEO + FREE TTS + CAPTIONS
# ============================================================

OUTPUT_DIR = Path("phase3e_output")
OUTPUT_DIR.mkdir(exist_ok=True)

VIDEO_INPUT = Path("phase3d2_output/sixscontent_phase3d2.mp4")
AUDIO_FILE = OUTPUT_DIR / "voiceover.mp3"
CAPTION_FILE = OUTPUT_DIR / "captions.srt"
FINAL_VIDEO = OUTPUT_DIR / "sixscontent_phase3e.mp4"

SCRIPT = """
Think about the last time you bought popcorn at the movies.

A small costs four dollars.
A large costs seven.

Seven dollars for popcorn feels like a total rip-off, right?

So you would probably stick with the small.

Now enter the medium popcorn for six dollars and fifty cents.

Suddenly, that seven dollar large doesn't feel expensive anymore.

It feels like a steal.

For just fifty cents extra, you get the biggest size.

This psychological pricing strategy is called the Decoy Effect.

The medium size isn't really designed to sell.

It acts as bait, making the highest price look like an irresistible bargain.

You see this everywhere.

Tech upgrades.
Coffee sizes.
Streaming subscriptions.
And even fast food menus.

Next time you see an unbelievable deal, ask yourself:

Did I actually want the expensive option?

Or did the decoy make me choose it?
""".strip()


def run_command(command, description):
    print(f"\n🔧 {description}")

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    if result.returncode != 0:
        print(result.stdout)
        raise RuntimeError(f"{description} failed.")

    return result.stdout


def check_ffmpeg():
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        if result.returncode == 0:
            print("✅ FFmpeg is available.")
        else:
            raise RuntimeError()

    except Exception:
        print("❌ FFmpeg is not available.")
        sys.exit(1)


def install_tts():
    print("🔊 Installing free TTS engine...")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--quiet",
            "edge-tts"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    if result.returncode != 0:
        print(result.stdout)
        raise RuntimeError("edge-tts installation failed.")

    print("✅ Free TTS installed.")


def create_voiceover():
    print("\n🎙️ Creating voice-over...")

    command = [
        sys.executable,
        "-m",
        "edge_tts",
        "--voice",
        "en-US-GuyNeural",
        "--text",
        SCRIPT,
        "--write-media",
        str(AUDIO_FILE)
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    if result.returncode != 0:
        print(result.stdout)
        raise RuntimeError("Voice-over generation failed.")

    if not AUDIO_FILE.exists():
        raise RuntimeError("Voice-over file was not created.")

    print(f"✅ Voice-over created: {AUDIO_FILE}")
    print(f"   Size: {AUDIO_FILE.stat().st_size:,} bytes")


def get_audio_duration():
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(AUDIO_FILE)
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError("Could not determine audio duration.")

    return float(result.stdout.strip())


def create_srt(duration):
    print("\n📝 Creating captions...")

    sentences = [
        "Think about the last time you bought popcorn at the movies.",
        "A small costs four dollars. A large costs seven.",
        "Seven dollars for popcorn feels like a total rip-off, right?",
        "So you would probably stick with the small.",
        "Now enter the medium popcorn for six dollars and fifty cents.",
        "Suddenly, that seven dollar large doesn't feel expensive anymore.",
        "It feels like a steal.",
        "For just fifty cents extra, you get the biggest size.",
        "This psychological pricing strategy is called the Decoy Effect.",
        "The medium size isn't really designed to sell.",
        "It acts as bait, making the highest price look like an irresistible bargain.",
        "You see this everywhere.",
        "Tech upgrades. Coffee sizes. Streaming subscriptions.",
        "And even fast food menus.",
        "Did I actually want the expensive option?",
        "Or did the decoy make me choose it?"
    ]

    total_words = sum(len(x.split()) for x in sentences)

    current = 0.0

    def timestamp(seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    with open(CAPTION_FILE, "w", encoding="utf-8") as f:

        for index, sentence in enumerate(sentences, start=1):

            words = len(sentence.split())

            segment_duration = max(
                1.5,
                duration * (words / total_words)
            )

            start = current
            end = min(duration, current + segment_duration)

            f.write(f"{index}\n")
            f.write(
                f"{timestamp(start)} --> {timestamp(end)}\n"
            )
            f.write(sentence)
            f.write("\n\n")

            current = end

    print(f"✅ Captions created: {CAPTION_FILE}")


def create_final_video():
    print("\n🎬 Combining:")
    print("   Pexels video")
    print("   Voice-over")
    print("   Captions")

    if not VIDEO_INPUT.exists():
        raise RuntimeError(
            f"Input video not found: {VIDEO_INPUT}"
        )

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(VIDEO_INPUT),
        "-i",
        str(AUDIO_FILE),

        "-filter_complex",
        (
            "[0:v]"
            "scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,"
            "setsar=1,"
            f"subtitles={CAPTION_FILE}:"
            "force_style='FontName=Arial,"
            "FontSize=18,"
            "Bold=1,"
            "Alignment=2,"
            "MarginV=150,"
            "Outline=3,"
            "Shadow=1'"
            "[v]"
        ),

        "-map",
        "[v]",

        "-map",
        "1:a",

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

        str(FINAL_VIDEO)
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    if result.returncode != 0:
        print(result.stdout)
        raise RuntimeError("Final video creation failed.")

    if not FINAL_VIDEO.exists():
        raise RuntimeError("Final video was not created.")

    print("✅ Final video created.")


def inspect_video():
    print("\n🔍 Checking final video...")

    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-show_entries",
        "stream=width,height,codec_name",
        "-of",
        "default=noprint_wrappers=1",
        str(FINAL_VIDEO)
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    print(result.stdout)


def main():

    print("=" * 60)
    print("🎬 SIXSCONTENT — PHASE 3E")
    print("PEXELS + FREE TTS + CAPTIONS")
    print("=" * 60)

    print("🚫 Telegram disabled.")
    print("🚫 Gemini disabled.")
    print("🚫 LTX disabled.")
    print("💰 Target cost: $0")
    print("⏱️ GitHub runs only when manually started.")

    check_ffmpeg()

    if not VIDEO_INPUT.exists():
        print(
            "\n❌ Phase 3D-2 video is missing:"
            f"\n   {VIDEO_INPUT}"
        )
        print(
            "\nPhase 3E expects the Phase 3D-2 video "
            "to be available in this GitHub run."
        )
        sys.exit(1)

    install_tts()

    create_voiceover()

    duration = get_audio_duration()

    print(f"🎙️ Voice-over duration: {duration:.2f} seconds")

    create_srt(duration)

    create_final_video()

    inspect_video()

    print("\n" + "=" * 60)
    print("PHASE 3E RESULT")
    print("=" * 60)

    print("✅ Pexels video loaded")
    print("✅ Free AI voice-over created")
    print("✅ Captions generated")
    print("✅ Captions burned into video")
    print("✅ Audio added")
    print("✅ Vertical 1080 × 1920 output")
    print(f"✅ Final video: {FINAL_VIDEO}")
    print(
        f"✅ Final size: "
        f"{FINAL_VIDEO.stat().st_size:,} bytes"
    )

    print("=" * 60)
    print("🔥 PHASE 3E SUCCESS!")
    print("=" * 60)
    print("GitHub will now stop automatically.")
    print("No 24/7 process is running.")


if __name__ == "__main__":
    main()
