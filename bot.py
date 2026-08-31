import os
import re
import sys
import time
import json
import math
import shutil
import asyncio
import subprocess
from pathlib import Path

import requests
from google import genai


# ============================================================
# SIXSCONTENT — UNIFIED VIDEO BOT
#
# Telegram
#   ↓
# Gemini
#   ↓
# Pexels
#   ↓
# Edge TTS
#   ↓
# Captions
#   ↓
# FFmpeg
#   ↓
# Telegram
# ============================================================


print("=" * 70)
print("🔥 SIXSCONTENT — UNIFIED VIDEO ENGINE")
print("=" * 70)


# ============================================================
# ENVIRONMENT
# ============================================================

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
GEMINI_KEY = os.environ["GEMINI_API_KEY"]
PEXELS_API_KEY = os.environ["PEXELS_API_KEY"]

TELEGRAM_API = (
    f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
)

client = genai.Client(
    api_key=GEMINI_KEY
)


# ============================================================
# MODELS
# ============================================================

MODELS = [
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite"
]


# ============================================================
# DIRECTORIES
# ============================================================

WORK_DIR = Path("sixscontent_work")
DOWNLOAD_DIR = WORK_DIR / "downloads"
CLIPS_DIR = WORK_DIR / "clips"

FINAL_VIDEO = (
    WORK_DIR /
    "sixscontent_final.mp4"
)

SCRIPT_FILE = (
    WORK_DIR /
    "script.txt"
)

VOICE_FILE = (
    WORK_DIR /
    "voiceover.mp3"
)

CAPTIONS_FILE = (
    WORK_DIR /
    "captions.srt"
)

METADATA_FILE = (
    WORK_DIR /
    "content_metadata.json"
)


# ============================================================
# CATEGORY RULES
# ============================================================

CATEGORY_RULES = {

    "body": """
NICHE: HUMAN BODY AND ANATOMY

Create fascinating content about:
- Human anatomy
- Strange things the body does
- How organs work
- Biological mechanisms
- Evolution
- Survival mechanisms
- Unexpected body facts

Avoid diagnosis, treatment advice, or dangerous medical claims.
""",

    "money": """
NICHE: MONEY AND BUSINESS

Create fascinating content about:
- Money psychology
- Business
- Consumer psychology
- Interesting financial history
- Business strategies
- How companies make money
- Economic concepts

Do not promise viewers they will become rich.
Do not give personalized financial advice.
Do not promote scams, gambling, or get-rich-quick schemes.
""",

    "psychology": """
NICHE: PSYCHOLOGY AND HUMAN BEHAVIOR

Create fascinating content about:
- Human behavior
- Cognitive biases
- Social psychology
- Memory
- Decision making
- Habits
- Communication
- Psychological experiments

Do not diagnose viewers.
Focus on established psychological concepts.
""",

    "world": """
NICHE: WORLD, HISTORY AND GEOGRAPHY

Create fascinating content about:
- Strange places
- Hidden history
- Countries
- Geography
- Historical events
- Ancient civilizations
- Unusual traditions
- Interesting cultures
- Weird but real places

Avoid fake facts.
Avoid invented historical events.
""",

    "science": """
NICHE: SCIENCE

Create fascinating content about:
- Space
- Physics
- Chemistry
- Biology
- Animals
- Earth
- Technology
- Scientific discoveries
- Strange natural phenomena

Explain difficult ideas simply.
Do not present speculation as proven fact.
"""
}


# ============================================================
# TELEGRAM
# ============================================================

def telegram_request(
    method,
    data=None,
    files=None,
    timeout=120
):

    url = f"{TELEGRAM_API}/{method}"

    response = requests.post(
        url,
        data=data,
        files=files,
        timeout=timeout
    )

    return response


def send_message(chat_id, text):

    max_length = 3900

    for i in range(
        0,
        len(text),
        max_length
    ):

        part = text[
            i:i + max_length
        ]

        try:

            response = requests.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": part
                },
                timeout=60
            )

            if response.status_code != 200:

                print(
                    "Telegram message error:",
                    response.text
                )

        except Exception as e:

            print(
                f"Telegram send error: {e}"
            )


def send_video(video):

    print("=" * 70)
    print("📲 SENDING FINAL VIDEO TO TELEGRAM")
    print("=" * 70)

    size_mb = (
        video.stat().st_size /
        1024 /
        1024
    )

    print(
        f"📦 Video size: {size_mb:.2f} MB"
    )

    if size_mb > 49:

        raise RuntimeError(
            "Final video is larger than 49 MB."
        )

    send_message(
        TELEGRAM_CHAT_ID,
        """
🔥 SIXSCONTENT VIDEO READY

The complete video pipeline has finished.

🎬 Uploading the final MP4 now...
"""
    )

    caption = """
🔥 SIXSCONTENT — FINAL VIDEO

✅ Gemini content
✅ Pexels visuals
✅ Voice-over
✅ Synchronized captions
✅ 1080×1920 vertical
✅ Final editing complete

Ready for:
TikTok
Instagram Reels
YouTube Shorts
Facebook Reels
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

        raise RuntimeError(
            f"Telegram upload exception: {e}"
        )

    if response.status_code != 200:

        raise RuntimeError(
            "Telegram video upload failed.\n"
            f"HTTP {response.status_code}\n"
            f"{response.text}"
        )

    result = response.json()

    if not result.get("ok"):

        raise RuntimeError(
            f"Telegram rejected video:\n{result}"
        )

    print(
        "✅ VIDEO SUCCESSFULLY DELIVERED TO TELEGRAM"
    )


# ============================================================
# FFMPEG
# ============================================================

def run_command(command):

    print(
        "▶️",
        " ".join(
            str(x)
            for x in command
        )
    )

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    print(
        result.stdout
    )

    if result.returncode != 0:

        raise RuntimeError(
            "Command failed."
        )


def check_ffmpeg():

    if shutil.which("ffmpeg") is None:

        raise RuntimeError(
            "FFmpeg is not installed."
        )

    if shutil.which("ffprobe") is None:

        raise RuntimeError(
            "FFprobe is not installed."
        )

    print(
        "✅ FFmpeg available."
    )

    print(
        "✅ FFprobe available."
    )


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

    try:

        return float(
            result.stdout.strip()
        )

    except Exception:

        return 0.0


# ============================================================
# GEMINI
# ============================================================

def build_prompt(category):

    return f"""
You are the lead short-form video creator for SIXSCONTENT.

Your job is NOT to write a school-style article.

Your job is to create a short-form video that makes people
stop scrolling immediately and keeps them watching.

CATEGORY:

{CATEGORY_RULES[category]}

RETENTION RULES:

1. The first sentence must create curiosity immediately.
2. The first 1–2 seconds must feel impossible to ignore.
3. Never start with:
   "Today we are going to..."
   "Did you know..."
   "In this video..."
4. Do not waste time introducing the topic.
5. Use short conversational sentences.
6. Keep the narration energetic.
7. Avoid long explanations.
8. Create a curiosity gap.
9. Give information in stages.
10. Add a surprising development before the ending.
11. The ending must pay off the opening.
12. The viewer should constantly feel:
    "Wait, what?"
    or
    "I need to know what happens next."
13. Target approximately 35–55 seconds.
14. Do NOT force the script to reach 60 seconds.
15. Use approximately 115–145 spoken words per minute.
16. Write for a fast narrator.
17. Avoid unnecessary filler.
18. Every sentence must earn its place.

VISUAL RULES:

Each visual must directly represent what the narrator is saying.

Do NOT give generic visuals such as:
"person walking"
"person thinking"
"businessman working"

unless they genuinely represent the narration.

Visuals should change frequently.

Create 8–12 scenes.

Each scene must contain:
- exact narration covered by the scene
- a highly specific Pexels search query

The visual query should describe something that could realistically
exist as stock footage.

VOICE:

Write natural spoken English.

Use punctuation for natural emphasis.

Avoid giant paragraphs.

OUTPUT VALID JSON ONLY.

Use this exact structure:

{{
  "category": "{category}",
  "title": "short curiosity-driven title",
  "hook": "opening hook",
  "script": "complete narration",
  "scenes": [
    {{
      "narration": "sentence or short section",
      "visual": "specific stock footage search query"
    }}
  ],
  "caption": "short social caption",
  "hashtags": ["#one", "#two", "#three"]
}}

Do not include markdown fences.
Do not include explanations outside the JSON.
"""


def extract_json(text):

    text = text.strip()

    if text.startswith("```"):

        text = re.sub(
            r"^```(?:json)?",
            "",
            text,
            flags=re.IGNORECASE
        )

        text = re.sub(
            r"```$",
            "",
            text
        )

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:

        raise ValueError(
            "Gemini did not return JSON."
        )

    return json.loads(
        text[start:end + 1]
    )


def generate_content(category):

    prompt = build_prompt(
        category
    )

    last_error = None

    for model in MODELS:

        print(
            f"🤖 Trying Gemini model: {model}"
        )

        for attempt in range(1, 3):

            try:

                response = (
                    client.models.generate_content(
                        model=model,
                        contents=prompt
                    )
                )

                if not response:

                    raise RuntimeError(
                        "Empty Gemini response."
                    )

                text = (
                    response.text
                    or ""
                ).strip()

                if not text:

                    raise RuntimeError(
                        "Gemini returned empty text."
                    )

                content = extract_json(
                    text
                )

                if not content.get(
                    "script"
                ):

                    raise RuntimeError(
                        "Gemini response has no script."
                    )

                scenes = content.get(
                    "scenes",
                    []
                )

                if len(scenes) < 4:

                    raise RuntimeError(
                        "Gemini returned too few scenes."
                    )

                print(
                    f"✅ Gemini succeeded with {model}"
                )

                return content

            except Exception as e:

                last_error = str(e)

                print(
                    f"⚠️ Gemini error: {e}"
                )

                temporary = (
                    "429" in str(e)
                    or "500" in str(e)
                    or "502" in str(e)
                    or "503" in str(e)
                    or "504" in str(e)
                    or "UNAVAILABLE" in str(e)
                    or "high demand" in str(e)
                )

                if temporary and attempt < 2:

                    delay = 5 * attempt

                    print(
                        f"Waiting {delay}s..."
                    )

                    time.sleep(
                        delay
                    )

                else:

                    break

    raise RuntimeError(
        "All Gemini models failed.\n"
        f"Last error: {last_error}"
    )


# ============================================================
# PEXELS
# ============================================================

def search_pexels(
    query,
    per_page=10
):

    print(
        f"🔎 Pexels: {query}"
    )

    response = requests.get(
        "https://api.pexels.com/v1/videos/search",
        headers={
            "Authorization":
            PEXELS_API_KEY
        },
        params={
            "query": query,
            "orientation": "portrait",
            "per_page": per_page
        },
        timeout=30
    )

    response.raise_for_status()

    return response.json().get(
        "videos",
        []
    )


def choose_pexels_video(videos):

    if not videos:

        return None

    # Prefer portrait footage.
    portrait = []

    for video in videos:

        width = video.get(
            "width",
            0
        )

        height = video.get(
            "height",
            0
        )

        if height > width:

            portrait.append(
                video
            )

    candidates = (
        portrait
        if portrait
        else videos
    )

    # Prefer reasonably large files.
    candidates.sort(
        key=lambda video: (
            video.get("height", 0),
            video.get("width", 0)
        ),
        reverse=True
    )

    return candidates[0]


def choose_download_link(video):

    files = video.get(
        "video_files",
        []
    )

    if not files:

        return None

    mp4 = [
        f for f in files
        if f.get("file_type")
        == "video/mp4"
    ]

    if not mp4:

        mp4 = files

    portrait = [
        f for f in mp4
        if f.get("height", 0)
        >= f.get("width", 0)
    ]

    candidates = (
        portrait
        if portrait
        else mp4
    )

    candidates.sort(
        key=lambda f: (
            f.get("width", 0) *
            f.get("height", 0)
        ),
        reverse=True
    )

    return candidates[0].get(
        "link"
    )


def download_file(
    url,
    output
):

    print(
        f"⬇️ Downloading {output.name}"
    )

    with requests.get(
        url,
        stream=True,
        timeout=120
    ) as response:

        response.raise_for_status()

        with open(
            output,
            "wb"
        ) as file:

            for chunk in response.iter_content(
                chunk_size=1024 * 1024
            ):

                if chunk:

                    file.write(
                        chunk
                    )


# ============================================================
# VISUAL BUILDING
# ============================================================

def clean_work_directory():

    if WORK_DIR.exists():

        shutil.rmtree(
            WORK_DIR
        )

    DOWNLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    CLIPS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


def build_visuals(content):

    scenes = content[
        "scenes"
    ]

    if len(scenes) > 10:

        scenes = scenes[:10]

    print("=" * 70)
    print("🎬 BUILDING VISUAL STORY")
    print("=" * 70)

    raw_files = []

    for index, scene in enumerate(
        scenes,
        start=1
    ):

        query = scene.get(
            "visual",
            ""
        ).strip()

        if not query:

            continue

        try:

            videos = search_pexels(
                query
            )

            selected = (
                choose_pexels_video(
                    videos
                )
            )

            if not selected:

                print(
                    f"⚠️ No footage for scene {index}"
                )

                continue

            link = (
                choose_download_link(
                    selected
                )
            )

            if not link:

                print(
                    f"⚠️ No download link for scene {index}"
                )

                continue

            output = (
                DOWNLOAD_DIR /
                f"scene_{index:02d}.mp4"
            )

            download_file(
                link,
                output
            )

            raw_files.append(
                output
            )

            print(
                f"✅ Scene {index} ready."
            )

        except Exception as e:

            print(
                f"⚠️ Scene {index} failed: {e}"
            )

    if not raw_files:

        raise RuntimeError(
            "No Pexels footage was downloaded."
        )

    return raw_files


# ============================================================
# VOICE
# ============================================================

def generate_voice(script):

    print("=" * 70)
    print("🎙️ GENERATING FAST VOICE-OVER")
    print("=" * 70)

    import edge_tts

    voice = (
        "en-US-ChristopherNeural"
    )

    SCRIPT_FILE.write_text(
        script,
        encoding="utf-8"
    )

    async def create():

        communicate = edge_tts.Communicate(
            script,
            voice,
            rate="+18%",
            volume="+0%"
        )

        await communicate.save(
            str(VOICE_FILE)
        )

    asyncio.run(
        create()
    )

    if not VOICE_FILE.exists():

        raise RuntimeError(
            "Voice-over was not created."
        )

    duration = get_duration(
        VOICE_FILE
    )

    print(
        f"✅ Voice-over created."
    )

    print(
        f"⏱️ Voice duration: "
        f"{duration:.2f}s"
    )

    return duration


# ============================================================
# CAPTIONS
# ============================================================

def srt_time(seconds):

    milliseconds = int(
        round(seconds * 1000)
    )

    hours = (
        milliseconds //
        3600000
    )

    milliseconds %= 3600000

    minutes = (
        milliseconds //
        60000
    )

    milliseconds %= 60000

    seconds_value = (
        milliseconds //
        1000
    )

    milliseconds %= 1000

    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{seconds_value:02d},"
        f"{milliseconds:03d}"
    )


def create_captions(
    script,
    audio_duration
):

    print("=" * 70)
    print("📝 CREATING SYNCHRONIZED CAPTIONS")
    print("=" * 70)

    words = script.split()

    if not words:

        raise RuntimeError(
            "Script contains no words."
        )

    # Short chunks make captions feel faster.
    chunks = []

    current = []

    for word in words:

    current.append(word)

    if len(current) >= 4:

        caption_text = " ".join(current)

        captions.append({
            "start": current_start,
            "end": current_end,
            "text": caption_text
        })

        current = []
        current_start = word_end
