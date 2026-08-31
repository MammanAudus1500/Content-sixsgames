import os
import sys
import json
import math
import shutil
import subprocess
from pathlib import Path


# ============================================================
# SIXSCONTENT — PHASE 3G
# HIGH-RETENTION VIDEO EDITOR
#
# INPUT:
#   Phase 3D-2 visual video
#   Phase 3E voice-over
#   Phase 3E captions
#
# OUTPUT:
#   Fast voice
#   Re-timed captions
#   Dynamic editing
#   Zoom / motion
#   1080x1920 MP4
# ============================================================

INPUT_VIDEO = Path(
    "phase3g_input/sixscontent_phase3d2.mp4"
)

INPUT_VOICE = Path(
    "phase3g_input/voiceover.mp3"
)

INPUT_SRT = Path(
    "phase3g_input/captions.srt"
)

OUTPUT_DIR = Path(
    "phase3g_output"
)

OUTPUT_VIDEO = OUTPUT_DIR / "sixscontent_phase3g.mp4"

OUTPUT_SRT = OUTPUT_DIR / "captions_fast.srt"

OUTPUT_METADATA = OUTPUT_DIR / "phase3g_metadata.json"


# ============================================================
# SETTINGS
# ============================================================

TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920

# Faster narration.
VOICE_SPEED = 1.25

# Visual movement.
ZOOM_MIN = 1.00
ZOOM_MAX = 1.10

# Keep shots short.
MAX_SHOT_SECONDS = 3.5

# Video quality.
CRF = "21"

FPS = 30


# ============================================================
# LOGGING
# ============================================================

def log(message=""):
    print(message, flush=True)


# ============================================================
# COMMAND RUNNER
# ============================================================

def run(command):

    log("")
    log("▶️ " + " ".join(str(x) for x in command))

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    print(result.stdout)

    if result.returncode != 0:

        raise RuntimeError(
            "Command failed."
        )


# ============================================================
# CHECK TOOLS
# ============================================================

def check_tools():

    log("🔧 Checking FFmpeg...")

    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "FFmpeg is not installed."
        )

    if shutil.which("ffprobe") is None:
        raise RuntimeError(
            "FFprobe is not installed."
        )

    log("✅ FFmpeg available.")
    log("✅ FFprobe available.")


# ============================================================
# FFPROBE
# ============================================================

def probe_duration(file):

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
        return float(
            result.stdout.strip()
        )
    except Exception:
        return 0.0


# ============================================================
# SRT PARSER
# ============================================================

def srt_time_to_seconds(value):

    value = value.replace(",", ".")

    hours, minutes, seconds = value.split(":")

    return (
        int(hours) * 3600
        + int(minutes) * 60
        + float(seconds)
    )


def seconds_to_srt_time(seconds):

    seconds = max(
        0.0,
        float(seconds)
    )

    hours = int(seconds // 3600)

    minutes = int(
        (seconds % 3600) // 60
    )

    secs = (
        seconds
        - hours * 3600
        - minutes * 60
    )

    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{secs:06.3f}"
        .replace(".", ",")
    )


def parse_srt(path):

    if not path.exists():

        raise RuntimeError(
            f"Missing SRT: {path}"
        )

    text = path.read_text(
        encoding="utf-8"
    )

    blocks = text.strip().split(
        "\n\n"
    )

    captions = []

    for block in blocks:

        lines = [
            line.strip()
            for line in block.splitlines()
            if line.strip()
        ]

        if len(lines) < 3:
            continue

        timing = lines[1]

        if "-->" not in timing:
            continue

        start_text, end_text = [
            x.strip()
            for x in timing.split("-->")
        ]

        start = srt_time_to_seconds(
            start_text
        )

        end = srt_time_to_seconds(
            end_text
        )

        caption_text = " ".join(
            lines[2:]
        )

        if end <= start:
            continue

        captions.append(
            {
                "start": start,
                "end": end,
                "text": caption_text
            }
        )

    return captions


# ============================================================
# CAPTION SPEED TRANSFORMATION
# ============================================================

def transform_captions(
    captions,
    speed
):

    transformed = []

    for item in captions:

        start = item["start"] / speed
        end = item["end"] / speed

        transformed.append(
            {
                "start": start,
                "end": end,
                "text": item["text"]
            }
        )

    return transformed


# ============================================================
# BREAK LONG CAPTIONS
# ============================================================

def split_caption_text(text):

    words = text.split()

    if len(words) <= 5:
        return text

    # Shorter phrases make captions easier
    # to read on mobile.
    midpoint = math.ceil(
        len(words) / 2
    )

    first = " ".join(
        words[:midpoint]
    )

    second = " ".join(
        words[midpoint:]
    )

    return first + "\n" + second


def improve_caption_blocks(captions):

    result = []

    for item in captions:

        duration = (
            item["end"]
            - item["start"]
        )

        text = split_caption_text(
            item["text"]
        )

        result.append(
            {
                "start": item["start"],
                "end": item["end"],
                "text": text
            }
        )

    return result


# ============================================================
# WRITE SRT
# ============================================================

def write_srt(captions, path):

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:

        for index, item in enumerate(
            captions,
            start=1
        ):

            file.write(
                f"{index}\n"
            )

            file.write(
                seconds_to_srt_time(
                    item["start"]
                )
            )

            file.write(
                " --> "
            )

            file.write(
                seconds_to_srt_time(
                    item["end"]
                )
            )

            file.write("\n")

            file.write(
                item["text"]
            )

            file.write("\n\n")


# ============================================================
# BUILD DYNAMIC VIDEO
# ============================================================

def create_dynamic_video(
    input_video,
    output_video,
    duration
):

    log("")
    log("=" * 60)
    log("🎬 BUILDING HIGH-RETENTION VIDEO")
    log("=" * 60)

    # We use one continuous filter so that
    # the video remains visually active.
    #
    # The crop slowly moves and zooms.
    # Different expressions are used over time.
    #
    # The source footage is repeated/looped if necessary
    # so the final video matches the narration length.

    vf = (
        "scale=1200:2133:force_original_aspect_ratio=increase,"
        "crop=1200:2133,"
        "zoompan="
        "z='1.0+0.08*sin(on/18)':"
        "x='(iw-iw/zoom)/2':"
        "y='(ih-ih/zoom)/2':"
        "d=1:"
        "s=1080x1920:"
        "fps=30,"
        "setsar=1"
    )

    run(
        [
            "ffmpeg",
            "-y",

            "-stream_loop",
            "-1",

            "-i",
            str(input_video),

            "-i",
            str(OUTPUT_DIR / "voice_fast.wav"),

            "-t",
            f"{duration:.3f}",

            "-map",
            "0:v:0",

            "-map",
            "1:a:0",

            "-vf",
            vf,

            "-r",
            str(FPS),

            "-c:v",
            "libx264",

            "-preset",
            "veryfast",

            "-crf",
            CRF,

            "-pix_fmt",
            "yuv420p",

            "-c:a",
            "aac",

            "-b:a",
            "128k",

            "-ar",
            "44100",

            "-movflags",
            "+faststart",

            str(output_video)
        ]
    )


# ============================================================
# CREATE FAST AUDIO
# ============================================================

def create_fast_voice(
    input_voice,
    output_voice
):

    log("")
    log("=" * 60)
    log("🎙️ SPEEDING UP VOICE")
    log("=" * 60)

    # atempo supports 0.5–2.0 per filter.
    # 1.25 = noticeably faster while
    # still sounding natural.

    run(
        [
            "ffmpeg",
            "-y",

            "-i",
            str(input_voice),

            "-filter:a",
            f"atempo={VOICE_SPEED}",

            "-ar",
            "44100",

            "-ac",
            "2",

            str(output_voice)
        ]
    )


# ============================================================
# CAPTION BURN-IN
# ============================================================

def burn_captions(
    input_video,
    output_video,
    srt_file
):

    log("")
    log("=" * 60)
    log("📝 BURNING SYNCHRONIZED CAPTIONS")
    log("=" * 60)

    # Escape the path for FFmpeg subtitles filter.
    subtitle_path = (
        str(srt_file.resolve())
        .replace("\\", "/")
        .replace(":", "\\:")
        .replace("'", "\\'")
    )

    subtitle_filter = (
        f"subtitles='{subtitle_path}':"
        "force_style="
        "'FontName=Arial,"
        "FontSize=18,"
        "Bold=1,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        "BorderStyle=1,"
        "Outline=3,"
        "Shadow=1,"
        "Alignment=2,"
        "MarginV=140'"
    )

    run(
        [
            "ffmpeg",
            "-y",

            "-i",
            str(input_video),

            "-vf",
            subtitle_filter,

            "-c:v",
            "libx264",

            "-preset",
            "veryfast",

            "-crf",
            "21",

            "-c:a",
            "copy",

            "-movflags",
            "+faststart",

            str(output_video)
        ]
    )


# ============================================================
# MAIN
# ============================================================

def main():

    log("=" * 60)
    log("🔥 SIXSCONTENT — PHASE 3G")
    log("HIGH-RETENTION EDITING ENGINE")
    log("=" * 60)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    check_tools()

    # --------------------------------------------------------
    # INPUT CHECK
    # --------------------------------------------------------

    log("")
    log("🔍 CHECKING INPUT FILES")

    required = [
        INPUT_VIDEO,
        INPUT_VOICE,
        INPUT_SRT
    ]

    for file in required:

        if not file.exists():

            raise RuntimeError(
                f"Required file missing: {file}"
            )

        log(
            f"✅ {file} "
            f"({file.stat().st_size:,} bytes)"
        )

    # --------------------------------------------------------
    # ORIGINAL DURATION
    # --------------------------------------------------------

    original_duration = probe_duration(
        INPUT_VOICE
    )

    log(
        f"🎙️ Original voice duration: "
        f"{original_duration:.2f}s"
    )

    # --------------------------------------------------------
    # FAST VOICE
    # --------------------------------------------------------

    fast_voice = OUTPUT_DIR / "voice_fast.wav"

    create_fast_voice(
        INPUT_VOICE,
        fast_voice
    )

    fast_duration = probe_duration(
        fast_voice
    )

    log(
        f"⚡ Fast voice duration: "
        f"{fast_duration:.2f}s"
    )

    # --------------------------------------------------------
    # CAPTIONS
    # --------------------------------------------------------

    log("")
    log("=" * 60)
    log("📝 RE-TIMING CAPTIONS")
    log("=" * 60)

    original_captions = parse_srt(
        INPUT_SRT
    )

    log(
        f"✅ Original captions: "
        f"{len(original_captions)}"
    )

    transformed = transform_captions(
        original_captions,
        VOICE_SPEED
    )

    improved = improve_caption_blocks(
        transformed
    )

    write_srt(
        improved,
        OUTPUT_SRT
    )

    log(
        f"✅ New captions: "
        f"{len(improved)}"
    )

    # --------------------------------------------------------
    # DYNAMIC VIDEO
    # --------------------------------------------------------

    dynamic_video = (
        OUTPUT_DIR /
        "dynamic_video.mp4"
    )

    create_dynamic_video(
        INPUT_VIDEO,
        dynamic_video,
        fast_duration
    )

    # --------------------------------------------------------
    # CAPTIONS
    # --------------------------------------------------------

    final_video = OUTPUT_VIDEO

    burn_captions(
        dynamic_video,
        final_video,
        OUTPUT_SRT
    )

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not final_video.exists():

        raise RuntimeError(
            "Final Phase 3G video was not created."
        )

    final_duration = probe_duration(
        final_video
    )

    final_size = (
        final_video.stat().st_size
    )

    metadata = {

        "project": "SixsContent",

        "phase": "3G",

        "status": "ready",

        "source": "Phase 3D-2",

        "original_voice_duration":
            round(original_duration, 3),

        "voice_speed":
            VOICE_SPEED,

        "final_voice_duration":
            round(fast_duration, 3),

        "final_video_duration":
            round(final_duration, 3),

        "resolution":
            "1080x1920",

        "orientation":
            "9:16",

        "dynamic_motion":
            True,

        "captions_regenerated":
            True,

        "caption_sync":
            "retimed to fast voice",

        "editing_style":
            "high-retention",

        "output":
            "sixscontent_phase3g.mp4"
    }

    OUTPUT_METADATA.write_text(
        json.dumps(
            metadata,
            indent=2
        ),
        encoding="utf-8"
    )

    log("")
    log("=" * 60)
    log("PHASE 3G RESULT")
    log("=" * 60)

    log("✅ Phase 3D-2 visual source loaded")
    log("✅ Voice-over accelerated")
    log("✅ Captions retimed")
    log("✅ Captions regenerated")
    log("✅ Dynamic motion applied")
    log("✅ Vertical 1080×1920 output")
    log("✅ Final video created")

    log(
        f"⏱️ Duration: "
        f"{final_duration:.2f}s"
    )

    log(
        f"💾 Size: "
        f"{final_size:,} bytes"
    )

    log(
        f"📁 Output: "
        f"{final_video}"
    )

    log("")
    log("🔥 PHASE 3G SUCCESS!")


if __name__ == "__main__":
    main()
