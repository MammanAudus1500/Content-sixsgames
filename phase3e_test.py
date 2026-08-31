import os
import sys
import subprocess
import asyncio
from pathlib import Path

INPUT_VIDEO = Path("phase3d2_output/sixscontent_phase3d2.mp4")
OUTPUT_DIR = Path("phase3e_output")
VOICE_FILE = OUTPUT_DIR / "voiceover.mp3"
CAPTION_FILE = OUTPUT_DIR / "captions.srt"
FINAL_VIDEO = OUTPUT_DIR / "sixscontent_phase3e.mp4"

VOICE = "en-US-ChristopherNeural"

# This is the script used for the Phase 3E test.
# Later, Phase 4 will automatically supply the real Gemini-generated script.
SCRIPT = """
Think about the last time you bought popcorn at the movies.

A small costs four dollars.
A large costs seven.

Seven dollars for popcorn feels like a total rip-off, right?

So you would probably stick with the small.

Now enter the medium popcorn for six dollars and fifty cents.

Suddenly, that seven-dollar large doesn't feel expensive anymore.
It feels like a steal.

For just fifty cents extra, you get the biggest size.

This psychological pricing strategy is called the decoy effect.

The medium option isn't necessarily designed to be the popular choice.
It can make the highest-priced option look much more attractive.

You see versions of this everywhere:
technology upgrades,
coffee sizes,
streaming subscriptions,
and fast food menus.

So next time you see an unbelievable deal,
ask yourself:

Did I actually want the expensive option,
or did the other options make it look like a bargain?
""".strip()


def run_command(command):
    print("▶️", " ".join(command))

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    print(result.stdout)

    if result.returncode != 0:
        print("❌ Command failed.")
        sys.exit(result.returncode)


def check_ffmpeg():
    print("🔧 Checking FFmpeg...")

    result = subprocess.run(
        ["ffmpeg", "-version"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        print("❌ FFmpeg is not available.")
        sys.exit(1)

    print("✅ FFmpeg is available.")


def check_input():
    print("🔎 Checking Phase 3D-2 video...")

    if not INPUT_VIDEO.exists():
        print("❌ Phase 3D-2 video is missing:")
        print(f"   {INPUT_VIDEO}")
        sys.exit(1)

    size = INPUT_VIDEO.stat().st_size

    if size < 100000:
        print("❌ Phase 3D-2 video appears invalid.")
        sys.exit(1)

    print(f"✅ Input video found.")
    print(f"   Size: {size:,} bytes")


async def create_voice():
    print("🎙️ Generating FREE voice-over with Edge TTS...")
    print(f"   Voice: {VOICE}")

    import edge_tts

    communicate = edge_tts.Communicate(
        SCRIPT,
        VOICE
    )

    await communicate.save(str(VOICE_FILE))

    if not VOICE_FILE.exists():
        print("❌ Voice-over was not created.")
        sys.exit(1)

    print(
        f"✅ Voice-over created "
        f"({VOICE_FILE.stat().st_size:,} bytes)"
    )


def create_srt():
    print("📝 Creating captions...")

    # Approximate timing for the test script.
    # Phase 4 will generate timing more intelligently.
    sentences = [
        "Think about the last time you bought popcorn at the movies.",
        "A small costs four dollars. A large costs seven.",
        "Seven dollars for popcorn feels like a total rip-off, right?",
        "So you would probably stick with the small.",
        "Now enter the medium popcorn for six dollars and fifty cents.",
        "Suddenly, that seven-dollar large doesn't feel expensive anymore.",
        "It feels like a steal.",
        "For just fifty cents extra, you get the biggest size.",
        "This psychological pricing strategy is called the decoy effect.",
        "The medium option isn't necessarily designed to be the popular choice.",
        "It can make the highest-priced option look much more attractive.",
        "You see versions of this everywhere:",
        "technology upgrades, coffee sizes, streaming subscriptions, and fast food menus.",
        "So next time you see an unbelievable deal, ask yourself:",
        "Did I actually want the expensive option, or did the other options make it look like a bargain?"
    ]

    durations = [
        4.0,
        3.5,
        3.5,
        2.5,
        4.0,
        3.5,
        2.0,
        3.0,
        3.5,
        3.5,
        3.5,
        2.0,
        4.0,
        4.0,
        3.0
    ]

    def timestamp(seconds):
        total_ms = int(seconds * 1000)

        hours = total_ms // 3600000
        total_ms %= 3600000

        minutes = total_ms // 60000
        total_ms %= 60000

        secs = total_ms // 1000
        millis = total_ms % 1000

        return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

    current = 0.0

    lines = []

    for index, (sentence, duration) in enumerate(
        zip(sentences, durations),
        start=1
    ):
        start = current
        end = current + duration

        lines.append(str(index))
        lines.append(
            f"{timestamp(start)} --> {timestamp(end)}"
        )
        lines.append(sentence)
        lines.append("")

        current = end

    CAPTION_FILE.write_text(
        "\n".join(lines),
        encoding="utf-8"
    )

    print(f"✅ Captions created: {CAPTION_FILE}")


def get_duration(file):
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(file)
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        return 0.0

    try:
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def create_final_video():
    print("🎬 Combining video + voice-over + captions...")

    filter_text = (
        "subtitles=captions.srt:"
        "force_style="
        "'FontName=Arial,"
        "FontSize=18,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        "BorderStyle=1,"
        "Outline=2,"
        "Shadow=1,"
        "Alignment=2,"
        "MarginV=120'"
    )

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(INPUT_VIDEO),
        "-i",
        str(VOICE_FILE),
        "-filter_complex",
        f"[0:v]{filter_text}[v]",
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

    # Run from the output directory so subtitles.srt resolves correctly.
    result = subprocess.run(
        command,
        cwd=str(OUTPUT_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    print(result.stdout)

    if result.returncode != 0:
        print("❌ FFmpeg failed while creating final video.")
        sys.exit(result.returncode)

    if not FINAL_VIDEO.exists():
        print("❌ Final video was not created.")
        sys.exit(1)

    print(
        f"✅ Final video created "
        f"({FINAL_VIDEO.stat().st_size:,} bytes)"
    )


def verify_final_video():
    print("🔍 Checking final video...")

    duration = get_duration(FINAL_VIDEO)

    print(f"   Duration: {duration:.2f} seconds")

    if duration <= 0:
        print("❌ Final video duration could not be detected.")
        sys.exit(1)

    print("============================================================")
    print("PHASE 3E RESULT")
    print("============================================================")
    print("✅ Phase 3D-2 video loaded automatically")
    print("✅ FREE voice-over generated")
    print("✅ Captions generated")
    print("✅ Voice-over + captions combined")
    print("✅ Final MP4 created")
    print(f"✅ Final video: {FINAL_VIDEO}")
    print(f"✅ Final size: {FINAL_VIDEO.stat().st_size:,} bytes")
    print(f"✅ Duration: {duration:.2f} seconds")
    print("============================================================")
    print("🔥 PHASE 3E SUCCESS!")
    print("============================================================")
    print("GitHub will now stop automatically.")
    print("No 24/7 process is running.")


def main():
    print("============================================================")
    print("🎬 SIXSCONTENT — PHASE 3E")
    print("PEXELS + FREE TTS + CAPTIONS")
    print("============================================================")
    print("🚫 Telegram disabled.")
    print("🚫 Gemini disabled.")
    print("🚫 LTX disabled.")
    print("💰 Target cost: $0")
    print("⏱️ GitHub runs only when manually started.")
    print()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    check_ffmpeg()
    check_input()

    asyncio.run(create_voice())

    create_srt()

    create_final_video()

    verify_final_video()


if __name__ == "__main__":
    main()
