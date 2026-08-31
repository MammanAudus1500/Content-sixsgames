import os
import time
import requests
from google import genai

# ============================================================
# SIXSCONTENT — PHASE 2
# ON-DEMAND TELEGRAM → GITHUB → GEMINI
# ============================================================

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
GEMINI_KEY = os.environ["GEMINI_API_KEY"]

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

client = genai.Client(api_key=GEMINI_KEY)


# ============================================================
# GEMINI MODEL FALLBACK SYSTEM
# ============================================================

MODELS = [
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite"
]


# ============================================================
# TELEGRAM
# ============================================================

def send_message(chat_id, text):

    url = f"{TELEGRAM_API}/sendMessage"

    # Telegram maximum message size is around 4096 characters.
    max_length = 3900

    for i in range(0, len(text), max_length):

        part = text[i:i + max_length]

        try:
            requests.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": part
                },
                timeout=30
            )

        except Exception as e:

            print(f"Telegram send error: {e}")


def get_updates(offset=None, timeout=20):

    url = f"{TELEGRAM_API}/getUpdates"

    params = {
        "timeout": timeout
    }

    if offset is not None:
        params["offset"] = offset

    response = requests.get(
        url,
        params=params,
        timeout=timeout + 10
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# CONTENT CATEGORIES
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

The viewer should think:

"Wait... my body actually does that?"
""",

    "money": """
NICHE: MONEY AND BUSINESS

Create fascinating content about:
- Money psychology
- Business
- Wealth behavior
- Consumer psychology
- Interesting financial history
- Business strategies
- How companies make money
- Economic concepts
- Interesting money facts

Do NOT promise viewers they will become rich.

Do NOT give personalized financial advice.

Do NOT promote scams, gambling, or get-rich-quick schemes.

Make it educational, surprising and curiosity-driven.
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
- Why people behave in surprising ways

Do not diagnose viewers.

Do not claim normal behavior proves someone has a mental disorder.

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

The viewer should think:

"I never knew that."
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

Explain difficult ideas in simple language.

Prefer established scientific information.

Do not present speculation as proven fact.
"""
}


# ============================================================
# GEMINI PROMPT
# ============================================================

def build_prompt(category):

    return f"""
You are the lead short-form content writer for SIXSCONTENT.

Your job is to create ONE highly engaging short-form video.

CATEGORY RULES:

{CATEGORY_RULES[category]}

STYLE:

- The first sentence must immediately create curiosity.
- The hook must work within approximately 3 seconds.
- No boring introduction.
- Do not say "Today we are going to..."
- Use natural conversational English.
- Make it sound like a real human narrator.
- Do not sound like a school textbook.
- Focus on ONE central idea.
- Do not combine unrelated facts.
- Make the viewer want to watch until the end.
- Suitable for TikTok, YouTube Shorts and Instagram Reels.
- Target approximately 45–70 seconds of narration.
- Make the script easy to turn into video scenes.
- Do not invent statistics.
- Do not invent studies.
- Do not invent quotations.
- Do not invent historical events.
- Do not make unsupported scientific claims.
- Avoid overused generic viral facts when possible.
- Give the topic a fresh angle.

OUTPUT EXACTLY LIKE THIS:

🔥 SIXSCONTENT RESULT

CATEGORY:
{category}

TITLE:
[short curiosity-driven title]

HOOK:
[powerful 1–2 sentence hook]

SCRIPT:
[45–70 second voice-over script]

VISUALS:
1. [visual scene]
2. [visual scene]
3. [visual scene]
4. [visual scene]
5. [visual scene]
6. [visual scene]

CAPTION:
[short social media caption]

HASHTAGS:
[8–12 relevant hashtags]

DURATION:
[recommended video duration]

THUMBNAIL IDEA:
[strong thumbnail concept]

FINAL CHECK:
Before answering, silently check that the information is plausible and that you have not invented facts or evidence.
"""


# ============================================================
# GEMINI REQUEST WITH RETRIES + FALLBACK MODELS
# ============================================================

def generate_content(category):

    prompt = build_prompt(category)

    last_error = None

    for model in MODELS:

        print(f"Trying Gemini model: {model}")

        # Try each model up to 2 times.
        for attempt in range(1, 3):

            try:

                print(
                    f"Attempt {attempt}/2 using {model}"
                )

                response = client.models.generate_content(
                    model=model,
                    contents=prompt
                )

                if response and response.text:

                    print(
                        f"SUCCESS using {model}"
                    )

                    return response.text

                last_error = "Gemini returned an empty response."

            except Exception as e:

                last_error = str(e)

                print(
                    f"Gemini error using {model}: {e}"
                )

                error_text = str(e)

                # Retry temporary/server errors.
                temporary_error = (
                    "503" in error_text
                    or "UNAVAILABLE" in error_text
                    or "429" in error_text
                    or "500" in error_text
                    or "502" in error_text
                    or "504" in error_text
                    or "high demand" in error_text
                )

                if temporary_error and attempt < 2:

                    delay = 5 * (2 ** (attempt - 1))

                    print(
                        f"Temporary Gemini problem."
                        f" Waiting {delay} seconds..."
                    )

                    time.sleep(delay)

                    continue

                # If model doesn't exist or is unavailable,
                # move immediately to the next model.
                break

    raise RuntimeError(
        "All Gemini models failed.\n\n"
        f"Last error:\n{last_error}"
    )


# ============================================================
# COMMAND HANDLER
# ============================================================

def handle_message(chat_id, text):

    text = text.strip()

    # --------------------------------------------------------
    # START
    # --------------------------------------------------------

    if text == "/start":

        send_message(
            chat_id,
            """
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

The system generates:

• Title
• Hook
• Script
• Visual directions
• Caption
• Hashtags
• Duration
• Thumbnail idea

⚡ Send /create when you're ready.
"""
        )

        return False


    # --------------------------------------------------------
    # HELP
    # --------------------------------------------------------

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
"""
        )

        return False


    # --------------------------------------------------------
    # CREATE
    # --------------------------------------------------------

    if text.startswith("/create"):

        parts = text.split()

        if len(parts) != 2:

            send_message(
                chat_id,
                """
❌ Invalid command.

Use:

/create body
/create money
/create psychology
/create world
/create science
"""
            )

            return False


        category = parts[1].lower()

        if category not in CATEGORY_RULES:

            send_message(
                chat_id,
                """
❌ Unknown category.

Available:

/create body
/create money
/create psychology
/create world
/create science
"""
            )

            return False


        names = {

            "body": "🧠 HUMAN BODY",

            "money": "💰 MONEY & BUSINESS",

            "psychology": "🧠 PSYCHOLOGY",

            "world": "🌍 WORLD",

            "science": "🔬 SCIENCE"
        }


        send_message(
            chat_id,
            f"""
🔥 Creating your {names[category]} video...

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

            result = generate_content(category)

            send_message(
                chat_id,
                f"""
{result}

✅ CONTENT CREATED SUCCESSFULLY

GitHub will now shut down automatically.

When you need another piece of content:

1. Start the GitHub Action again.
2. Send your /create command.
"""
            )

            # IMPORTANT:
            # Return True so the GitHub program exits.
            return True


        except Exception as e:

            send_message(
                chat_id,
                f"""
❌ Gemini could not create the content.

The system tried multiple Gemini models and retries.

Error:
{str(e)}

GitHub will now shut down automatically.
"""
            )

            # Also stop GitHub after failure.
            return True


    # --------------------------------------------------------
    # UNKNOWN COMMAND
    # --------------------------------------------------------

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

    return False


# ============================================================
# MAIN
# ============================================================

def main():

    print("🔥 SIXSCONTENT PHASE 2 STARTED")

    print("Waiting for Telegram command...")

    # --------------------------------------------------------
    # CLEAR OLD TELEGRAM UPDATES
    # --------------------------------------------------------

    offset = None

    try:

        old_updates = get_updates(
            timeout=1
        )

        if old_updates.get("ok"):

            results = old_updates.get(
                "result",
                []
            )

            if results:

                offset = (
                    results[-1]["update_id"] + 1
                )

                print(
                    "Old Telegram messages cleared."
                )

    except Exception as e:

        print(
            f"Could not clear old messages: {e}"
        )


    # --------------------------------------------------------
    # WAIT FOR ONE NEW COMMAND
    # --------------------------------------------------------

    while True:

        try:

            data = get_updates(
                offset=offset,
                timeout=20
            )

            if not data.get("ok"):

                time.sleep(2)

                continue


            updates = data.get(
                "result",
                []
            )


            for update in updates:

                offset = (
                    update["update_id"] + 1
                )

                message = update.get(
                    "message"
                )

                if not message:

                    continue


                chat_id = message["chat"]["id"]

                text = message.get(
                    "text",
                    ""
                )


                if not text:

                    continue


                print(
                    f"Telegram command: {text}"
                )


                should_stop = handle_message(
                    chat_id,
                    text
                )


                # ------------------------------------------------
                # AUTOMATICALLY STOP AFTER /create
                # ------------------------------------------------

                if should_stop:

                    print(
                        "🔥 Content request finished."
                    )

                    print(
                        "🛑 Stopping GitHub session."
                    )

                    return


        except requests.exceptions.RequestException as e:

            print(
                f"Telegram connection error: {e}"
            )

            time.sleep(5)


        except Exception as e:

            print(
                f"Unexpected error: {e}"
            )

            time.sleep(5)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()
