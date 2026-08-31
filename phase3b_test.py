import os
import re
import sys
import time
from pathlib import Path

import requests
from google import genai


# ============================================================
# SIXSCONTENT — PHASE 3B
# GEMINI → VISUAL SCENES → PEXELS
# ============================================================

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY is missing.")
    sys.exit(1)

if not PEXELS_API_KEY:
    print("❌ PEXELS_API_KEY is missing.")
    sys.exit(1)


# Current Gemini model
GEMINI_MODEL = "gemini-3.6-flash"

PEXELS_URL = "https://api.pexels.com/videos/search"

OUTPUT_DIR = Path("phase3b_clips")
OUTPUT_DIR.mkdir(exist_ok=True)

pexels_headers = {
    "Authorization": PEXELS_API_KEY
}

gemini_client = genai.Client(api_key=GEMINI_API_KEY)


# ============================================================
# TEST TOPIC
# ============================================================

TOPIC = "money"


# ============================================================
# ASK GEMINI FOR SCENE DESCRIPTIONS
# ============================================================

def create_content():

    print("\n🧠 Asking Gemini to create content...")

    prompt = f"""
Create a short-form viral video about {TOPIC}.

Return EXACTLY this structure:

TITLE:
[title]

HOOK:
[hook]

SCRIPT:
[voice-over script]

VISUALS:
1. [visual scene]
2. [visual scene]
3. [visual scene]
4. [visual scene]
5. [visual scene]
6. [visual scene]

CAPTION:
[caption]

HASHTAGS:
[hashtags]

DURATION:
[duration]

THUMBNAIL IDEA:
[thumbnail idea]

Important:
The VISUALS must describe real-world footage that could reasonably
be found on a stock video website such as Pexels.

Do not include impossible fantasy footage.
Do not include instructions to generate images.
"""

    try:

        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )

        text = response.text

        if not text:
            print("❌ Gemini returned empty content.")
            return None

        print("\n🔥 GEMINI CONTENT CREATED\n")
        print(text)

        return text

    except Exception as error:

        print("\n❌ Gemini error:")
        print(error)

        return None


# ============================================================
# EXTRACT VISUAL SCENES
# ============================================================

def extract_visuals(text):

    print("\n🎬 Extracting visual scenes...")

    match = re.search(
        r"VISUALS:\s*(.*?)(?:\n\s*CAPTION:|\n\s*HASHTAGS:|\Z)",
        text,
        re.IGNORECASE | re.DOTALL
    )

    if not match:
        print("❌ Could not find VISUALS section.")
        return []

    visuals_text = match.group(1)

    scenes = re.findall(
        r"(?:^|\n)\s*(?:\d+[\.\):]|[-•])\s*(.+)",
        visuals_text
    )

    scenes = [scene.strip() for scene in scenes if scene.strip()]

    if not scenes:
        print("❌ No visual scenes found.")

    print(f"✅ Found {len(scenes)} visual scenes.")

    for i, scene in enumerate(scenes, 1):
        print(f"{i}. {scene}")

    return scenes


# ============================================================
# TURN SCENE DESCRIPTION INTO SEARCH QUERY
# ============================================================

def make_search_query(scene):

    prompt = f"""
Convert this video scene description into a simple Pexels stock-video
search query.

Scene:
{scene}

Rules:
- Return ONLY the search query.
- Use 2 to 5 words.
- Describe a real-world subject or action.
- Do not use quotes.
- Do not use hashtags.
- Do not explain anything.

Example:
"Close-up of businessman checking financial charts"
→ businessman financial charts

Example:
"Person holding a phone while looking at a bank balance"
→ person checking bank phone
"""

    try:

        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )

        query = response.text.strip()

        query = query.replace('"', "")
        query = query.replace("'", "")

        query = re.sub(r"\s+", " ", query)

        # Keep it short.
        words = query.split()

        if len(words) > 5:
            query = " ".join(words[:5])

        return query

    except Exception as error:

        print(f"⚠️ Query generation failed: {error}")

        # Fallback: use first useful words from scene.
        words = re.findall(r"[A-Za-z0-9]+", scene)

        return " ".join(words[:4])


# ============================================================
# SEARCH PEXELS
# ============================================================

def search_pexels(query):

    print(f"\n🔎 Pexels search: {query}")

    params = {
        "query": query,
        "orientation": "portrait",
        "size": "medium",
        "per_page": 5,
    }

    try:

        response = requests.get(
            PEXELS_URL,
            headers=pexels_headers,
            params=params,
            timeout=30
        )

        print(f"HTTP: {response.status_code}")

        if response.status_code != 200:
            print("❌ Pexels error:")
            print(response.text)
            return None

        data = response.json()

        videos = data.get("videos", [])

        if not videos:
            print("⚠️ No portrait videos found.")

            # Retry without portrait restriction.
            fallback_params = {
                "query": query,
                "size": "medium",
                "per_page": 5,
            }

            fallback = requests.get(
                PEXELS_URL,
                headers=pexels_headers,
                params=fallback_params,
                timeout=30
            )

            if fallback.status_code == 200:
                videos = fallback.json().get("videos", [])

        if not videos:
            print("❌ No videos found.")
            return None

        return videos[0]

    except Exception as error:

        print(f"❌ Pexels request failed: {error}")

        return None


# ============================================================
# CHOOSE BEST VIDEO FILE
# ============================================================

def choose_video_file(video):

    files = video.get("video_files", [])

    if not files:
        return None

    # Prefer portrait.
    portrait = [
        file
        for file in files
        if (file.get("width") or 0) < (file.get("height") or 0)
    ]

    candidates = portrait if portrait else files

    # Prefer approximately 720p.
    candidates.sort(
        key=lambda file: (
            abs((file.get("height") or 0) - 1280),
            -(file.get("width") or 0)
        )
    )

    return candidates[0]


# ============================================================
# DOWNLOAD VIDEO
# ============================================================

def download_video(video, scene_number):

    video_file = choose_video_file(video)

    if not video_file:
        print("❌ No downloadable video file.")
        return False

    link = video_file.get("link")

    if not link:
        print("❌ No video download link.")
        return False

    output_file = OUTPUT_DIR / f"scene_{scene_number:02d}.mp4"

    print(
        f"⬇️ Downloading scene {scene_number}: "
        f"{video_file.get('width')}x{video_file.get('height')}"
    )

    try:

        with requests.get(
            link,
            stream=True,
            timeout=120
        ) as response:

            response.raise_for_status()

            with open(output_file, "wb") as file:

                for chunk in response.iter_content(
                    chunk_size=1024 * 1024
                ):

                    if chunk:
                        file.write(chunk)

        size_mb = output_file.stat().st_size / (1024 * 1024)

        print(
            f"✅ Scene {scene_number} saved "
            f"({size_mb:.2f} MB)"
        )

        return True

    except Exception as error:

        print(f"❌ Download failed: {error}")

        if output_file.exists():
            output_file.unlink()

        return False


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("SIXSCONTENT — PHASE 3B")
    print("GEMINI → PEXELS AUTOMATIC VIDEO SEARCH")
    print("=" * 70)

    content = create_content()

    if not content:
        sys.exit(1)

    scenes = extract_visuals(content)

    if not scenes:
        sys.exit(1)

    successful = 0

    for index, scene in enumerate(scenes, 1):

        print("\n" + "-" * 70)
        print(f"SCENE {index}")
        print("-" * 70)

        print(f"Description: {scene}")

        query = make_search_query(scene)

        print(f"🎯 Search query: {query}")

        video = search_pexels(query)

        if not video:
            print(f"⚠️ Scene {index} skipped.")
            continue

        print(f"✅ Pexels video ID: {video.get('id')}")
        print(f"🔗 Pexels page: {video.get('url')}")

        if download_video(video, index):
            successful += 1

        # Small delay to be polite to APIs.
        time.sleep(1)

    print("\n" + "=" * 70)
    print("PHASE 3B RESULT")
    print("=" * 70)

    print(f"Scenes found: {len(scenes)}")
    print(f"Clips downloaded: {successful}")

    if successful > 0:

        print("\n🔥 PHASE 3B SUCCESS!")
        print("Gemini successfully created visual scenes.")
        print("Pexels successfully found matching stock footage.")
        print("The clips are ready for Phase 3C.")

    else:

        print("\n❌ No clips were downloaded.")
        sys.exit(1)

    print("=" * 70)


if __name__ == "__main__":
    main()
