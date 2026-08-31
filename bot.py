import os
import requests
from google import genai
from google.genai import types

# ============================================================
# SIXSCONTENT BOT
# Telegram + Gemini
# ============================================================

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
GEMINI_KEY = os.environ["GEMINI_API_KEY"]

TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# Gemini client
client = genai.Client(api_key=GEMINI_KEY)

MODEL = "gemini-2.5-flash"


# ============================================================
# TELEGRAM FUNCTIONS
# ============================================================

def send_message(chat_id, text):
    try:
        requests.post(
            f"{TELEGRAM_URL}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
            },
            timeout=30,
        )
    except Exception as e:
        print("Telegram error:", e)


def get_updates(offset=None):
    params = {
        "timeout": 30,
    }

    if offset is not None:
        params["offset"] = offset

    response = requests.get(
        f"{TELEGRAM_URL}/getUpdates",
        params=params,
        timeout=40,
    )

    return response.json()


# ============================================================
# GEMINI CONTENT GENERATOR
# ============================================================

def create_content(category):

    category_prompts = {
        "body": """
Create a viral short-form video about the human body.

Focus on:
- surprising body facts
- health/science curiosity
- things people experience but don't understand

Do NOT give medical diagnosis or dangerous medical advice.
""",

        "money": """
Create a viral short-form video about money.

Focus on:
- money psychology
- financial habits
- surprising money facts
- business ideas
- common financial mistakes

Do not promise guaranteed profits.
""",

        "psychology": """
Create a viral short-form video about psychology.

Focus on:
- human behavior
- social psychology
- habits
- relationships
- surprising psychological effects

Make it interesting and easy to understand.
""",

        "world": """
Create a viral short-form video about the world.

Focus on:
- strange places
- unusual countries
- history
- geography
- surprising facts
- things most people don't know
""",

        "science": """
Create a viral short-form video about science.

Focus on:
- space
- physics
- animals
- technology
- nature
- surprising scientific facts

Make the explanation simple enough for a general audience.
"""
    }

    selected_prompt = category_prompts.get(category)

    if not selected_prompt:
        return None

    prompt = f"""
You are the content creator for SixsContent.

{selected_prompt}

Create ONE highly engaging short-form video concept.

The video should be suitable for TikTok, YouTube Shorts and Instagram Reels.

Return EXACTLY this format:

TITLE:
[short viral title]

HOOK:
[one powerful opening sentence]

SCRIPT:
[30-60 second narration. Make it conversational and easy to understand.]

VISUALS:
[5-8 simple visual ideas that could be used while the narration plays]

CAPTION:
[short social-media caption]

HASHTAGS:
[5-8 relevant hashtags]

Rules:
- Do not use emojis excessively.
- Do not invent fake statistics.
- Do not claim something is scientifically proven if it is not.
- Make the hook immediately interesting.
- Keep the script easy to narrate.
- Make the content original.
"""

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.9,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                    disable=True
                ),
            ),
        )

        if response.text:
            return response.text.strip()

        return "Gemini returned an empty response."

    except Exception as e:
        print("Gemini error:", repr(e))
        return f"ERROR: {str(e)}"


# ============================================================
# COMMAND HANDLER
# ============================================================

def handle_message(chat_id, text):

    text = text.strip()

    if text == "/start":

        send_message(
            chat_id,
            """🔥 Welcome to SixsContent!

Your automated content machine is ready.

Use:

/create body
/create money
/create psychology
/create world
/create science

Example:

/create body

The bot will create a complete short-video concept for you."""
        )

        return

    if text.startswith("/create"):

        parts = text.split()

        if len(parts) < 2:

            send_message(
                chat_id,
                """Please choose a category.

Examples:

/create body
/create money
/create psychology
/create world
/create science"""
            )

            return

        category = parts[1].lower()

        valid_categories = [
            "body",
            "money",
            "psychology",
            "world",
            "science",
        ]

        if category not in valid_categories:

            send_message(
                chat_id,
                """❌ Unknown category.

Available categories:

body
money
psychology
world
science"""
            )

            return

        send_message(
            chat_id,
            f"""🧠 Creating your {category} video...

Gemini is generating the idea, hook, script and visuals.

Please wait..."""
        )

        result = create_content(category)

        if result.startswith("ERROR:"):

            send_message(
                chat_id,
                """❌ Gemini error occurred.

The request failed.

Check the GitHub Actions log for the exact error."""
            )

            return

        send_message(
            chat_id,
            "🔥 SIXSCONTENT VIDEO\n\n" + result
        )

        return

    send_message(
        chat_id,
        """I don't understand that command.

Use:

/start

or

/create body
/create money
/create psychology
/create world
/create science"""
    )


# ============================================================
# MAIN BOT LOOP
# ============================================================

def main():

    print("🔥 SixsContent Bot started")

    offset = None

    while True:

        try:

            data = get_updates(offset)

            if not data.get("ok"):
                print("Telegram API error:", data)
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

                print(
                    f"Message from {chat_id}: {text}"
                )

                handle_message(
                    chat_id,
                    text
                )

        except Exception as e:

            print(
                "Bot loop error:",
                repr(e)
            )


if __name__ == "__main__":
    main()
