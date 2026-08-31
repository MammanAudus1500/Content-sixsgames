import os
import re
import json
import time
import shutil
import asyncio
import subprocess
from pathlib import Path

import requests
from google import genai


# ============================================================
# SIXSCONTENT — SINGLE FILE VIDEO BOT
#
# TELEGRAM
#    ↓
# GEMINI
#    ↓
# PEXELS
#    ↓
# EDGE TTS
#    ↓
# CAPTIONS
#    ↓
# FFMPEG
#    ↓
# TELEGRAM
# ============================================================

print("=" * 70)
print("🔥 SIXSCONTENT — UNIFIED VIDEO BOT")
print("=" * 70)


# ============================================================
# ENVIRONMENT
# ============================================================

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
GEMINI_KEY = os.environ["GEMINI_API_KEY"]
PEXELS_API_KEY = os.environ["PEXELS_API_KEY"]


TELEGRAM_API = (
    f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
)


client = genai.Client(
    api_key=GEMINI_KEY
)


# ============================================================
# GEMINI MODELS
# ============================================================

MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash"
]


# ============================================================
# DIRECTORIES
# ============================================================

WORK_DIR = Path("sixscontent_work")

DOWNLOAD_DIR = (
    WORK_DIR / "downloads"
)

CLIPS_DIR = (
    WORK_DIR / "clips"
)

FINAL_VIDEO = (
    WORK_DIR / "sixscontent_final.mp4"
)

SCRIPT_FILE = (
    WORK_DIR / "script.txt"
)

VOICE_FILE = (
    WORK_DIR / "voiceover.mp3"
)

CAPTIONS_FILE = (
    WORK_DIR / "captions.srt"
)

METADATA_FILE = (
    WORK_DIR / "content_metadata.json"
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
# TELEGRAM FUNCTIONS
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


def send_message(
    chat_id,
    text
):

    if not chat_id:
        return

    max_length = 3900

    for start in range(
        0,
        len(text),
        max_length
    ):

        part = text[
            start:start + max_length
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


def send_video(
    chat_id,
    video
):

    if not video.exists():

        raise RuntimeError(
            "Final video does not exist."
        )

    size_mb = (
        video.stat().st_size
        / 1024
        / 1024
    )

    print(
        f"📦 Final video size: {size_mb:.2f} MB"
    )

    if size_mb > 49:

        raise RuntimeError(
            "Video is larger than Telegram's safe upload limit."
        )

    caption = (
        "🔥 SIXSCONTENT — FINAL VIDEO\n\n"
        "✅ Gemini script\n"
        "✅ Pexels visuals\n"
        "✅ Voice-over\n"
        "✅ Captions\n"
        "✅ Vertical 1080×1920\n"
        "✅ Final editing complete"
    )

    try:

        with open(
            video,
            "rb"
        ) as video_file:

            response = telegram_request(
                "sendVideo",
                data={
                    "chat_id": chat_id,
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
            "Telegram upload failed:\n"
            f"{response.text}"
        )

    result = response.json()

    if not result.get("ok"):

        raise RuntimeError(
            f"Telegram rejected video:\n{result}"
        )

    print(
        "✅ FINAL VIDEO SENT TO TELEGRAM"
    )


# ============================================================
# FFMPEG
# ============================================================

def run_command(
    command
):

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
            "FFmpeg command failed."
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


def get_duration(
    file
):

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
# GEMINI PROMPT
# ============================================================

def build_prompt(
    category
):

    return f"""
You are the lead short-form video creator for SIXSCONTENT.

Your job is to create a highly engaging short-form video.

CATEGORY:

{CATEGORY_RULES[category]}

RETENTION RULES:

1. The first sentence must immediately create curiosity.
2. Never start with "Today we are going to..."
3. Never start with "Did you know..."
4. Never waste time introducing the topic.
5. Use short conversational sentences.
6. Make the narration sound natural.
7. Build a curiosity gap.
8. Reveal information progressively.
9. Include a surprising development.
10. The ending should pay off the opening.
11. Avoid filler.
12. Every sentence must earn its place.
13. Target 45–70 seconds.
14. Aim for approximately 120–150 spoken words per minute.
15. Make the first 3 seconds especially strong.
16. Make visual changes frequent.
17. Visuals must directly relate to the narration.

CREATE 8–12 scenes.

Each scene needs:

- narration
- specific Pexels stock-footage search query

The visual search query must describe footage that could realistically
exist on a stock-video website.

OUTPUT VALID JSON ONLY.

Use exactly:

{{
  "category": "{category}",
  "title": "curiosity-driven title",
  "hook": "strong opening hook",
  "script": "complete narration",
  "scenes": [
    {{
      "narration": "short narration section",
      "visual": "specific stock video search query"
    }}
  ],
  "caption": "short social caption",
  "hashtags": [
    "#one",
    "#two",
    "#three"
  ]
}}

Do not use markdown.
Do not put JSON inside ``` fences.
"""


def extract_json(
    text
):

    text = text.strip()

    text = re.sub(
        r"^```json",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"^```",
        "",
        text
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
            "Gemini did not return valid JSON."
        )

    return json.loads(
        text[
            start:end + 1
        ]
    )


def generate_content(
    category
):

    prompt = build_prompt(
        category
    )

    last_error = None

    for model in MODELS:

        print(
            f"🤖 Gemini model: {model}"
        )

        for attempt in range(
            1,
            3
        ):

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

                script = (
                    content.get(
                        "script",
                        ""
                    ).strip()
                )

                scenes = content.get(
                    "scenes",
                    []
                )

                if not script:

                    raise RuntimeError(
                        "Gemini returned no script."
                    )

                if len(scenes) < 4:

                    raise RuntimeError(
                        "Gemini returned too few scenes."
                    )

                print(
                    "✅ Gemini content created."
                )

                return content

            except Exception as e:

                last_error = str(e)

                print(
                    f"⚠️ Gemini error: {e}"
                )

                if attempt < 2:

                    time.sleep(
                        5
                    )

    raise RuntimeError(
        "Gemini failed.\n"
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
        f"🔎 Pexels search: {query}"
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
        timeout=40
    )

    response.raise_for_status()

    return response.json().get(
        "videos",
        []
    )


def choose_pexels_video(
    videos
):

    if not videos:

        return None

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

        if height >= width:

            portrait.append(
                video
            )

    candidates = (
        portrait
        if portrait
        else videos
    )

    candidates.sort(
        key=lambda video: (
            video.get(
                "height",
                0
            ),
            video.get(
                "width",
                0
            )
        ),
        reverse=True
    )

    return candidates[0]


def choose_download_link(
    video
):

    files = video.get(
        "video_files",
        []
    )

    if not files:

        return None

    mp4 = [
        item
        for item in files
        if item.get(
            "file_type"
        ) == "video/mp4"
    ]

    if not mp4:

        mp4 = files

    portrait = [
        item
        for item in mp4
        if item.get(
            "height",
            0
        ) >= item.get(
            "width",
            0
        )
    ]

    candidates = (
        portrait
        if portrait
        else mp4
    )

    candidates.sort(
        key=lambda item: (
            item.get(
                "width",
                0
            )
            *
            item.get(
                "height",
                0
            )
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
        timeout=180
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
# CLEAN WORKSPACE
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


# ============================================================
# DOWNLOAD VISUALS
# ============================================================

def build_visuals(
    content
):

    scenes = content.get(
        "scenes",
        []
    )

    if len(scenes) > 10:

        scenes = scenes[:10]

    downloaded = []

    print("=" * 70)
    print("🎬 DOWNLOADING VISUALS")
    print("=" * 70)

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

            selected = choose_pexels_video(
                videos
            )

            if not selected:

                print(
                    f"⚠️ No footage for scene {index}"
                )

                continue

            link = choose_download_link(
                selected
            )

            if not link:

                print(
                    f"⚠️ No download link for scene {index}"
                )

                continue

            output = (
                DOWNLOAD_DIR
                /
                f"scene_{index:02d}.mp4"
            )

            download_file(
                link,
                output
            )

            if output.exists():

                downloaded.append(
                    output
                )

                print(
                    f"✅ Scene {index} downloaded."
                )

        except Exception as e:

            print(
                f"⚠️ Scene {index} failed: {e}"
            )

    if not downloaded:

        raise RuntimeError(
            "No Pexels videos were downloaded."
        )

    return downloaded


# ============================================================
# VOICEOVER
# ============================================================

def generate_voice(
    script
):

    print("=" * 70)
    print("🎙️ GENERATING VOICE")
    print("=" * 70)

    import edge_tts

    voice = (
        "en-US-ChristopherNeural"
    )

    SCRIPT_FILE.write_text(
        script,
        encoding="utf-8"
    )

    async def create_voice():

        communicate = edge_tts.Communicate(
            script,
            voice,
            rate="+12%",
            volume="+0%"
        )

        await communicate.save(
            str(VOICE_FILE)
        )

    asyncio.run(
        create_voice()
    )

    if not VOICE_FILE.exists():

        raise RuntimeError(
            "Voice-over was not created."
        )

    duration = get_duration(
        VOICE_FILE
    )

    if duration <= 0:

        raise RuntimeError(
            "Voice-over duration could not be detected."
        )

    print(
        f"✅ Voice-over created: {duration:.2f}s"
    )

    return duration


# ============================================================
# CAPTIONS
# ============================================================

def srt_time(
    seconds
):

    milliseconds = int(
        round(
            seconds * 1000
        )
    )

    hours = (
        milliseconds
        // 3600000
    )

    milliseconds %= 3600000

    minutes = (
        milliseconds
        // 60000
    )

    milliseconds %= 60000

    seconds_value = (
        milliseconds
        // 1000
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
    print("📝 CREATING CAPTIONS")
    print("=" * 70)

    words = script.split()

    if not words:

        raise RuntimeError(
            "Script contains no words."
        )

    chunks = []

    current = []

    for word in words:

        current.append(
            word
        )

        # Keep captions short.
        if (
            len(current) >= 5
            or word.endswith(
                (".", "!", "?")
            )
        ):

            chunks.append(
                " ".join(
                    current
                )
            )

            current = []

    if current:

        chunks.append(
            " ".join(
                current
            )
        )

    if not chunks:

        raise RuntimeError(
            "Could not create caption chunks."
        )

    chunk_duration = (
        audio_duration
        /
        len(chunks)
    )

    lines = []

    for index, caption_text in enumerate(
        chunks
    ):

        start = (
            index
            *
            chunk_duration
        )

        end = min(
            audio_duration,
            (
                index + 1
            )
            *
            chunk_duration
        )

        lines.append(
            f"{index + 1}\n"
            f"{srt_time(start)} --> "
            f"{srt_time(end)}\n"
            f"{caption_text}\n"
        )

    CAPTIONS_FILE.write_text(
        "\n".join(lines),
        encoding="utf-8"
    )

    print(
        f"✅ {len(chunks)} caption blocks created."
    )

    return CAPTIONS_FILE


# ============================================================
# MAKE EACH CLIP VERTICAL
# ============================================================

def prepare_clip(
    source,
    output,
    duration
):

    command = [
        "ffmpeg",
        "-y",
        "-stream_loop",
        "-1",
        "-i",
        str(source),
        "-t",
        str(duration),
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
        "24",
        "-pix_fmt",
        "yuv420p",
        str(output)
    ]

    run_command(
        command
    )


# ============================================================
# BUILD VIDEO
# ============================================================

def build_final_video(
    visuals,
    audio_duration
):

    print("=" * 70)
    print("🎥 BUILDING FINAL VIDEO")
    print("=" * 70)

    if not visuals:

        raise RuntimeError(
            "No visuals available."
        )

    clip_duration = (
        audio_duration
        /
        len(visuals)
    )

    prepared_clips = []

    for index, visual in enumerate(
        visuals,
        start=1
    ):

        output = (
            CLIPS_DIR
            /
            f"clip_{index:02d}.mp4"
        )

        print(
            f"🎬 Preparing clip {index}"
        )

        prepare_clip(
            visual,
            output,
            clip_duration
        )

        prepared_clips.append(
            output
        )

    concat_file = (
        WORK_DIR
        /
        "concat.txt"
    )

    with open(
        concat_file,
        "w",
        encoding="utf-8"
    ) as file:

        for clip in prepared_clips:

            safe_path = (
                str(
                    clip.resolve()
                )
                .replace(
                    "'",
                    "'\\''"
                )
            )

            file.write(
                f"file '{safe_path}'\n"
            )

    silent_video = (
        WORK_DIR
        /
        "silent_video.mp4"
    )

    run_command(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-t",
            str(audio_duration),
            "-c",
            "copy",
            str(silent_video)
        ]
    )

    print(
        "🎙️ Adding voice-over..."
    )

    run_command(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(silent_video),
            "-i",
            str(VOICE_FILE),
            "-t",
            str(audio_duration),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-shortest",
            str(FINAL_VIDEO)
        ]
    )

    if not FINAL_VIDEO.exists():

        raise RuntimeError(
            "Final video was not created."
        )

    print(
        "✅ FINAL VIDEO CREATED"
    )

    return FINAL_VIDEO


# ============================================================
# SAVE METADATA
# ============================================================

def save_metadata(
    content,
    duration
):

    metadata = dict(
        content
    )

    metadata[
        "duration_seconds"
    ] = duration

    METADATA_FILE.write_text(
        json.dumps(
            metadata,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )


# ============================================================
# COMPLETE PIPELINE
# ============================================================

def create_video(
    category,
    chat_id
):

    print("=" * 70)
    print(
        f"🔥 STARTING {category.upper()} VIDEO"
    )
    print("=" * 70)

    clean_work_directory()

    send_message(
        chat_id,
        "🤖 Creating the script with Gemini..."
    )

    content = generate_content(
        category
    )

    title = content.get(
        "title",
        "SixsContent Video"
    )

    script = content.get(
        "script",
        ""
    )

    print(
        f"📝 TITLE: {title}"
    )

    print(
        f"📝 SCRIPT:\n{script}"
    )

    send_message(
        chat_id,
        f"✅ Script created.\n\n🎬 {title}\n\n"
        "⬇️ Downloading visuals..."
    )

    visuals = build_visuals(
        content
    )

    send_message(
        chat_id,
        f"✅ Downloaded {len(visuals)} visual clips.\n\n"
        "🎙️ Creating voice-over..."
    )

    voice_duration = generate_voice(
        script
    )

    send_message(
        chat_id,
        f"✅ Voice-over created ({voice_duration:.1f}s).\n\n"
        "📝 Creating captions..."
    )

    create_captions(
        script,
        voice_duration
    )

    save_metadata(
        content,
        voice_duration
    )

    send_message(
        chat_id,
        "🎥 Editing final vertical video..."
    )

    final_video = build_final_video(
        visuals,
        voice_duration
    )

    send_message(
        chat_id,
        "✅ Video editing finished.\n\n"
        "📲 Sending the final video..."
    )

    send_video(
        chat_id,
        final_video
    )

    send_message(
        chat_id,
        "🔥 DONE!\n\n"
        f"🎬 {title}\n"
        f"⏱️ {voice_duration:.1f} seconds\n\n"
        "The final video has been sent above."
    )


# ============================================================
# TELEGRAM BOT
# ============================================================

def telegram_get_updates(
    offset=None
):

    params = {
        "timeout": 30
    }

    if offset is not None:

        params[
            "offset"
        ] = offset

    response = requests.get(
        f"{TELEGRAM_API}/getUpdates",
        params=params,
        timeout=40
    )

    response.raise_for_status()

    data = response.json()

    if not data.get("ok"):

        return []

    return data.get(
        "result",
        []
    )


def send_category_menu(
    chat_id
):

    keyboard = {
        "inline_keyboard": [

            [
                {
                    "text": "🌍 World",
                    "callback_data": "category_world"
                }
            ],

            [
                {
                    "text": "🧠 Psychology",
                    "callback_data": "category_psychology"
                }
            ],

            [
                {
                    "text": "🧬 Human Body",
                    "callback_data": "category_body"
                }
            ],

            [
                {
                    "text": "💰 Money & Business",
                    "callback_data": "category_money"
                }
            ],

            [
                {
                    "text": "🔬 Science",
                    "callback_data": "category_science"
                }
            ]

        ]
    }

    requests.post(
        f"{TELEGRAM_API}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": (
                "🔥 SIXSCONTENT\n\n"
                "Choose the type of video you want me to create:"
            ),
            "reply_markup": keyboard
        },
        timeout=60
    )


def answer_callback(
    callback_id
):

    try:

        requests.post(
            f"{TELEGRAM_API}/answerCallbackQuery",
            json={
                "callback_query_id":
                callback_id
            },
            timeout=30
        )

    except Exception as e:

        print(
            "Callback error:",
            e
        )


# ============================================================
# COMMAND HANDLER
# ============================================================

def handle_message(
    message
):

    chat = message.get(
        "chat",
        {}
    )

    chat_id = chat.get(
        "id"
    )

    text = (
        message.get(
            "text",
            ""
        )
        .strip()
        .lower()
    )

    if not chat_id:

        return

    print(
        f"📩 Telegram message: {text}"
    )

    if text in (
        "/start",
        "/create"
    ):

        send_category_menu(
            chat_id
        )

        return

    if text.startswith(
        "/create "
    ):

        category = text.split(
            " ",
            1
        )[1].strip()

        if category in CATEGORY_RULES:

            start_pipeline_safe(
                category,
                chat_id
            )

        else:

            send_message(
                chat_id,
                "❌ Unknown category.\n\n"
                "Use /start and choose a category."
            )

        return

    if text in (
        "/world",
        "/createworld"
    ):

        start_pipeline_safe(
            "world",
            chat_id
        )

        return

    if text in (
        "/science",
        "/createscience"
    ):

        start_pipeline_safe(
            "science",
            chat_id
        )

        return

    if text in (
        "/psychology",
        "/createpsychology"
    ):

        start_pipeline_safe(
            "psychology",
            chat_id
        )

        return

    if text in (
        "/body",
        "/createbody"
    ):

        start_pipeline_safe(
            "body",
            chat_id
        )

        return

    if text in (
        "/money",
        "/createmoney"
    ):

        start_pipeline_safe(
            "money",
            chat_id
        )

        return

    send_message(
        chat_id,
        "🔥 SIXSCONTENT\n\n"
        "Use /start to create a new video."
    )


# ============================================================
# CALLBACK HANDLER
# ============================================================

def handle_callback(
    callback
):

    callback_id = callback.get(
        "id"
    )

    data = callback.get(
        "data",
        ""
    )

    message = callback.get(
        "message",
        {}
    )

    chat = message.get(
        "chat",
        {}
    )

    chat_id = chat.get(
        "id"
    )

    answer_callback(
        callback_id
    )

    if not chat_id:

        return

    if data.startswith(
        "category_"
    ):

        category = data.replace(
            "category_",
            "",
            1
        )

        if category not in CATEGORY_RULES:

            send_message(
                chat_id,
                "❌ Invalid category."
            )

            return

        start_pipeline_safe(
            category,
            chat_id
        )


# ============================================================
# SAFE PIPELINE START
# ============================================================

def start_pipeline_safe(
    category,
    chat_id
):

    send_message(
        chat_id,
        (
            f"🔥 Starting {category.upper()} video...\n\n"
            "This can take a few minutes because the bot is "
            "creating the script, downloading footage, "
            "generating voice and rendering the video."
        )
    )

    try:

        create_video(
            category,
            chat_id
        )

    except Exception as e:

        print("=" * 70)
        print("❌ PIPELINE ERROR")
        print("=" * 70)

        print(
            repr(e)
        )

        send_message(
            chat_id,
            (
                "❌ VIDEO CREATION FAILED\n\n"
                f"Error: {e}\n\n"
                "The bot is still running. "
                "Use /start to try again."
            )
        )


# ============================================================
# BOT LOOP
# ============================================================

def run_bot():

    print("=" * 70)
    print("🤖 TELEGRAM BOT STARTING")
    print("=" * 70)

    check_ffmpeg()

    # Remove any old webhook.
    try:

        requests.get(
            f"{TELEGRAM_API}/deleteWebhook",
            params={
                "drop_pending_updates": False
            },
            timeout=30
        )

    except Exception as e:

        print(
            "Webhook cleanup warning:",
            e
        )

    offset = None

    print(
        "✅ Telegram polling started."
    )

    while True:

        try:

            updates = telegram_get_updates(
                offset
            )

            for update in updates:

                offset = (
                    update["update_id"]
                    + 1
                )

                if "message" in update:

                    handle_message(
                        update["message"]
                    )

                elif "callback_query" in update:

                    handle_callback(
                        update["callback_query"]
                    )

        except KeyboardInterrupt:

            print(
                "🛑 Bot stopped."
            )

            break

        except Exception as e:

            print(
                "⚠️ Telegram polling error:",
                e
            )

            time.sleep(
                5
            )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    run_bot()
