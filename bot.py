import os
import time
import requests

from google import genai
from google.genai import types


# ============================================================
# SIXSCONTENT - ON DEMAND TELEGRAM BOT
# One GitHub Action run handles one content request, then exits.
# ============================================================

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
GEMINI_KEY = os.environ["GEMINI_API_KEY"]

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

GEMINI_MODEL = "gemini-2.5-flash"

# How long GitHub waits for your Telegram command.
# After this time, the bot shuts down automatically.
WAIT_TIME_SECONDS = 10 * 60


client = genai.Client(api_key=GEMINI_KEY)


# ============================================================
# TELEGRAM
# ============================================================

def telegram_get_updates(offset=None):

    params = {
        "timeout": 20
    }

    if offset is not None:
        params["offset"] = offset

    response = requests.get(
        f"{TELEGRAM_API}/getUpdates",
        params=params,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def send_message(chat_id, text):

    if len(text) > 4000:
        text = text[:3950] + "\n\n[Message shortened]"

    response = requests.post(
        f"{TELEGRAM_API}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text
        },
        timeout=30
    )

    response.raise_for_status()


# ============================================================
# GEMINI
# ============================================================

def generate_content(category):

    category_description = {

        "body": """
Create an interesting viral short-form video about the human body,
health science, anatomy, or surprising body facts.
Do not diagnose diseases or give dangerous medical advice.
""",

        "money": """
Create an interesting viral short-form video about money,
money psychology, business, financial habits, or surprising
financial facts.
Do not promise guaranteed profits or present risky financial
advice as guaranteed.
""",

        "psychology": """
Create an interesting viral short-form video about psychology,
human behavior, habits, social behavior, relationships, or
surprising psychological effects.
""",

        "world": """
Create an interesting viral short-form video about the world,
geography, countries, history, unusual places, cultures,
or surprising facts about our planet.
""",

        "science": """
Create an interesting viral short-form video about science,
space, animals, physics, technology, nature, or surprising
scientific discoveries.
"""
    }

    prompt = f"""
You are the main content creator for SixsContent.

CATEGORY:
{category}

TOPIC DIRECTION:
{category_description[category]}

Create ONE highly engaging short-form video.

The content will be used for TikTok, YouTube Shorts and Instagram Reels.

Make it:
- attention-grabbing
- easy to understand
- factual
- suitable for a general audience
- approximately 30-60 seconds when narrated

Return exactly this format:

TITLE:
A short clickable title.

HOOK:
A powerful first sentence that makes people want to keep watching.

SCRIPT:
Write the complete narration for the video.
Make it conversational and engaging.

VISUALS:
Give 6 simple visual directions for the video.
Number them 1 to 6.

CAPTION:
Write a short social-media caption.

HASHTAGS:
Give 8 relevant hashtags.

IMPORTANT:
Do not invent statistics.
Do not claim something is scientifically proven unless it is established.
Do not give dangerous medical or financial instructions.
Do not use excessive emojis.
"""

    try:

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.9,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                    disable=True
                )
            )
        )

        if not response.text:
            return None, "Gemini returned an empty response."

        return response.text.strip(), None

    except Exception as error:

        print("GEMINI ERROR:")
        print(repr(error))

        return None, str(error)


# ============================================================
# COMMAND PROCESSING
# ============================================================

VALID_CATEGORIES = {
    "body",
    "money",
    "psychology",
    "world",
    "science"
}


def process_command(chat_id, text):

    text = text.strip()

    print(f"Telegram command received: {text}")

    if text == "/start":

        send_message(
            chat_id,
            """🔥 Welcome to SixsContent!

Your on-demand content machine is ready.

Available commands:

/create body
/create money
/create psychology
/create world
/create science

This GitHub session will automatically stop after the job is finished."""
        )

        return "continue"

    if not text.startswith("/create"):

        send_message(
            chat_id,
            """❌ Unknown command.

Use:

/create body
/create money
/create psychology
/create world
/create science"""
        )

        return "continue"

    parts = text.split()

    if len(parts) != 2:

        send_message(
            chat_id,
            """❌ Please choose one category.

Examples:

/create body
/create money
/create psychology
/create world
/create science"""
        )

        return "continue"

    category = parts[1].lower()

    if category not in VALID_CATEGORIES:

        send_message(
            chat_id,
            """❌ Invalid category.

Available:

body
money
psychology
world
science"""
        )

        return "continue"

    # Tell the user that generation has started.
    send_message(
        chat_id,
        f"""🧠 Creating your {category} video...

Gemini is preparing:

• Title
• Hook
• Script
• Visual directions
• Caption
• Hashtags

Please wait..."""
    )

    content, error = generate_content(category)

    if error:

        print("GENERATION FAILED:")
        print(error)

        send_message(
            chat_id,
            f"""❌ Gemini failed to create the content.

Error:
{error}

The GitHub session will now stop."""
        )

        return "done"

    send_message(
        chat_id,
        "🔥 SIXSCONTENT RESULT\n\n" + content
    )

    send_message(
        chat_id,
        """✅ Content created successfully.

GitHub will now shut down this session.

When you want another piece of content, start the GitHub Action again."""
    )

    return "done"


# ============================================================
# WAIT FOR TELEGRAM
# ============================================================

def main():

    print("========================================")
    print("🔥 SIXSCONTENT ON-DEMAND BOT")
    print("========================================")
    print("Bot started.")
    print("Waiting for Telegram command...")
    print(f"Maximum waiting time: {WAIT_TIME_SECONDS} seconds")

    # Check Telegram connection.
    try:

        me = requests.get(
            f"{TELEGRAM_API}/getMe",
            timeout=20
        )

        me.raise_for_status()

        bot_info = me.json()

        print("Telegram connection: OK")
        print("Bot:", bot_info["result"].get("username"))

    except Exception as error:

        print("Telegram connection failed:")
        print(repr(error))
        return

    # --------------------------------------------------------
    # Get the latest update ID first.
    #
    # This prevents an old Telegram message from a previous
    # GitHub run from accidentally triggering this run.
    # --------------------------------------------------------

    try:

        initial = telegram_get_updates()

        updates = initial.get("result", [])

        if updates:

            offset = updates[-1]["update_id"] + 1

        else:

            offset = None

    except Exception as error:

        print("Could not initialize Telegram polling:")
        print(repr(error))
        return

    start_time = time.time()

    # --------------------------------------------------------
    # Temporary polling loop.
    #
    # IMPORTANT:
    # This is NOT a 24/7 loop.
    #
    # It automatically exits after:
    # - one successful /create command
    # - one failed generation
    # - 10 minutes with no command
    # --------------------------------------------------------

    while True:

        elapsed = time.time() - start_time

        if elapsed >= WAIT_TIME_SECONDS:

            print("No command received.")
            print("GitHub session is shutting down.")

            return

        try:

            data = telegram_get_updates(offset)

            if not data.get("ok"):

                print("Telegram returned an error:")
                print(data)

                time.sleep(3)

                continue

            updates = data.get("result", [])

            for update in updates:

                offset = update["update_id"] + 1

                message = update.get("message")

                if not message:
                    continue

                chat = message.get("chat")

                if not chat:
                    continue

                chat_id = chat["id"]

                text = message.get("text", "")

                if not text:
                    continue

                result = process_command(
                    chat_id,
                    text
                )

                if result == "done":

                    print("Job completed.")
                    print("SixsContent session shutting down.")

                    return

        except requests.exceptions.RequestException as error:

            print("Telegram network error:")
            print(repr(error))

            time.sleep(5)

        except Exception as error:

            print("BOT ERROR:")
            print(repr(error))

            time.sleep(5)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()
