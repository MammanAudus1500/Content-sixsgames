import os
import time
import requests
from google import genai

# ============================================================
# SIXSCONTENT — PHASE 2
# Telegram → GitHub Actions → Gemini → Telegram
# ============================================================

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
GEMINI_KEY = os.environ["GEMINI_API_KEY"]

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# Current Gemini Flash model
GEMINI_MODEL = "gemini-3.7-flash"

client = genai.Client(api_key=GEMINI_KEY)


# ============================================================
# TELEGRAM FUNCTIONS
# ============================================================

def send_message(chat_id, text):
    url = f"{TELEGRAM_API}/sendMessage"

    # Telegram has a message limit, so split very long responses.
    max_length = 4000

    for i in range(0, len(text), max_length):
        part = text[i:i + max_length]

        requests.post(
            url,
            json={
                "chat_id": chat_id,
                "text": part
            },
            timeout=30
        )


def get_updates(offset=None):
    url = f"{TELEGRAM_API}/getUpdates"

    params = {
        "timeout": 20
    }

    if offset is not None:
        params["offset"] = offset

    response = requests.get(
        url,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# CONTENT RULES
# ============================================================

CATEGORY_RULES = {

    "body": """
NICHE: HUMAN BODY / ANATOMY

Create fascinating short-form content about:
- Human anatomy
- Strange things the body does
- Amazing biological mechanisms
- Unusual body facts
- How organs work
- Evolution and survival mechanisms

Avoid medical diagnosis, treatment advice, or dangerous health claims.

The content should make viewers think:
"Wait... my body actually does that?"
""",

    "money": """
NICHE: MONEY / BUSINESS / WEALTH

Create fascinating short-form content about:
- Money psychology
- Business facts
- Wealth behavior
- Consumer psychology
- Interesting financial history
- Business strategies
- How companies make money
- Economic concepts explained simply

Do NOT promise viewers that they will become rich.
Do NOT give personalized financial advice.
Do NOT promote scams, gambling, or get-rich-quick schemes.

Make the content educational and curiosity-driven.
""",

    "psychology": """
NICHE: PSYCHOLOGY / HUMAN BEHAVIOR

Create fascinating short-form content about:
- Human behavior
- Cognitive biases
- Social psychology
- Memory
- Decision making
- Habits
- Communication
- Interesting psychological experiments
- Why people behave in surprising ways

Do not diagnose viewers or claim that one behavior proves a mental disorder.

Focus on scientifically supported concepts.
""",

    "world": """
NICHE: WORLD / HISTORY / GEOGRAPHY / CULTURE

Create fascinating short-form content about:
- Strange places
- Hidden history
- Interesting countries
- Unusual traditions
- Historical events
- Geography
- Ancient civilizations
- Surprising cultural facts
- Weird but real places around the world

Avoid obvious fake facts and sensational misinformation.

The goal is:
"I never knew that happened."
""",

    "science": """
NICHE: SCIENCE

Create fascinating short-form content about:
- Space
- Physics
- Chemistry
- Biology
- Animals
- Earth
- Technology
- Scientific discoveries
- Strange natural phenomena

Explain difficult concepts in simple language.

Prefer scientifically established information.
Avoid presenting speculation as fact.
"""
}


# ============================================================
# GEMINI PROMPT
# ============================================================

def create_content(category):

    rules = CATEGORY_RULES[category]

    prompt = f"""
You are the lead short-form content writer for SIXSCONTENT.

Your job is to create ONE highly engaging short-form video idea.

{rules}

IMPORTANT STYLE:

- The first sentence must immediately create curiosity.
- No boring introductions such as "Today we are going to..."
- The hook should work within the first 3 seconds.
- Make the viewer want to stay until the end.
- Use simple conversational English.
- Make it sound natural when spoken by a narrator.
- Do not write like a school textbook.
- Do not use fake statistics.
- Do not invent scientific studies.
- Do not exaggerate facts beyond what the evidence supports.
- Avoid repeating common viral facts unless you add a genuinely interesting angle.
- Make the story suitable for TikTok, YouTube Shorts and Instagram Reels.
- Target approximately 45–70 seconds of narration.
- Keep the script easy to turn into AI-generated visuals.

VERY IMPORTANT:
The script should contain ONE central idea.
Do not combine several unrelated facts.

OUTPUT EXACTLY IN THIS FORMAT:

🔥 SIXSCONTENT RESULT

CATEGORY:
[category]

TITLE:
[short curiosity-driven title]

HOOK:
[powerful 1–2 sentence hook]

SCRIPT:
[45–70 second narration]

VISUALS:
1. [scene 1]
2. [scene 2]
3. [scene 3]
4. [scene 4]
5. [scene 5]
6. [scene 6]

CAPTION:
[short social-media caption]

HASHTAGS:
[8–12 relevant hashtags]

DURATION:
[recommended duration]

THUMBNAIL IDEA:
[strong visual thumbnail concept]

FINAL QUALITY RULE:
Before answering, silently check that the information is plausible and that you have not invented facts, studies, statistics, quotations, or historical events.

Category requested:
{category}
"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt
    )

    return response.text


# ============================================================
# COMMAND HANDLER
# ============================================================

def handle_message(chat_id, text):

    text = text.strip()

    if text == "/start":

        message = """
🔥 Welcome to SixsContent!

Your automated content machine is ready.

PHASE 2 is active.

Create content with:

/create body
/create money
/create psychology
/create world
/create science

Example:

/create body

The system will generate:
• Title
• Hook
• Script
• Visual directions
• Caption
• Hashtags
• Duration
• Thumbnail idea

⚡ Start whenever you need content.
"""

        send_message(chat_id, message)
        return


    if text == "/help":

        send_message(
            chat_id,
            """
🔥 SIXSCONTENT COMMANDS

/create body
/create money
/create psychology
/create world
/create science

/start
/help

Use one /create command at a time.
"""
        )

        return


    if text.startswith("/create"):

        parts = text.split()

        if len(parts) != 2:

            send_message(
                chat_id,
                """
❌ Invalid command.

Use one of:

/create body
/create money
/create psychology
/create world
/create science
"""
            )

            return


        category = parts[1].lower()

        if category not in CATEGORY_RULES:

            send_message(
                chat_id,
                """
❌ Unknown category.

Available categories:

/create body
/create money
/create psychology
/create world
/create science
"""
            )

            return


        category_names = {
            "body": "🧠 HUMAN BODY",
            "money": "💰 MONEY & BUSINESS",
            "psychology": "🧠 PSYCHOLOGY",
            "world": "🌍 WORLD",
            "science": "🔬 SCIENCE"
        }

        send_message(
            chat_id,
            f"""
🔥 Creating your {category_names[category]} video...

Gemini is preparing:

• Viral title
• Strong hook
• Voice-over script
• Scene-by-scene visuals
• Caption
• Hashtags
• Duration
• Thumbnail idea

Please wait...
"""
        )


        try:

            result = create_content(category)

            final_message = f"""
🔥 SIXSCONTENT RESULT

{result}

✅ Content created successfully.

GitHub will now shut down this session.

When you want another piece of content,
start the GitHub Action again.
"""

            send_message(chat_id, final_message)

        except Exception as e:

            error_message = f"""
❌ Gemini failed to create the content.

Error:
{str(e)}

The GitHub session will now stop.
"""

            send_message(chat_id, error_message)

        return


    send_message(
        chat_id,
        """
❌ I don't understand that command.

Use:

/create body
/create money
/create psychology
/create world
/create science
"""
    )


# ============================================================
# MAIN LOOP
# ============================================================

def main():

    print("🔥 SixsContent Phase 2 started")

    offset = None

    # Tell Telegram to ignore old messages.
    try:

        data = get_updates()

        if data.get("ok") and data.get("result"):

            offset = data["result"][-1]["update_id"] + 1

    except Exception:

        pass


    # GitHub Actions stays alive ONLY while this workflow is running.
    # When the workflow is cancelled, GitHub stops it.

    while True:

        try:

            data = get_updates(offset)

            if not data.get("ok"):
                time.sleep(2)
                continue


            for update in data.get("result", []):

                offset = update["update_id"] + 1

                message = update.get("message")

                if not message:
                    continue

                chat_id = message["chat"]["id"]

                text = message.get("text", "")

                if not text:
                    continue

                print(f"Telegram message: {text}")

                handle_message(chat_id, text)


        except requests.exceptions.RequestException as e:

            print(f"Telegram connection error: {e}")
            time.sleep(5)


        except Exception as e:

            print(f"Unexpected error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
