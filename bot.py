import os
import requests
from google import genai

# =========================
# CONFIG
# =========================

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
GEMINI_KEY = os.environ["GEMINI_API_KEY"]

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

client = genai.Client(api_key=GEMINI_KEY)


# =========================
# TELEGRAM
# =========================

def send_message(chat_id, text):
    requests.post(
        f"{TELEGRAM_API}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text
        },
        timeout=30
    )


# =========================
# GEMINI
# =========================

def create_content(niche):

    prompt = f"""
You are the content strategist for a short-form educational
content channel.

Niche: {niche}

Create ONE original short-video idea.

The video should be:
- Interesting
- Educational
- Easy to understand
- Suitable for YouTube Shorts, TikTok and Facebook Reels
- Approximately 30-60 seconds
- Not misleading
- Not copied from another creator

Return exactly:

TITLE:
HOOK:
SCRIPT:
CAPTION:
HASHTAGS:

For health/body topics, do not diagnose people,
do not give dangerous medical advice, and clearly
present medical facts as general education.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return response.text


# =========================
# BOT
# =========================

def main():

    offset = None

    print("SixsContent AI Bot is running...")

    while True:

        response = requests.get(
            f"{TELEGRAM_API}/getUpdates",
            params={
                "timeout": 30,
                "offset": offset
            },
            timeout=40
        )

        data = response.json()

        for update in data.get("result", []):

            offset = update["update_id"] + 1

            message = update.get("message")

            if not message:
                continue

            chat_id = message["chat"]["id"]
            text = message.get("text", "").strip()

            # START
            if text == "/start":

                send_message(
                    chat_id,
                    "🔥 Welcome to SixsContent!\n\n"
                    "Your automated content machine is ready.\n\n"
                    "Use:\n"
                    "/create body\n"
                    "/create money\n"
                    "/create psychology\n"
                    "/create world\n"
                    "/create science"
                )

            # CREATE
            elif text.startswith("/create"):

                niche = text.replace("/create", "").strip()

                if not niche:

                    send_message(
                        chat_id,
                        "Choose a niche.\n\n"
                        "Example:\n"
                        "/create body"
                    )

                    continue

                send_message(
                    chat_id,
                    f"🧠 Creating a {niche} video idea...\n\n"
                    "Please wait."
                )

                try:

                    content = create_content(niche)

                    send_message(
                        chat_id,
                        "🎬 CONTENT CREATED\n\n" + content
                    )

                except Exception as e:

                    print("Gemini error:", e)

                    send_message(
                        chat_id,
                        "❌ Gemini error occurred.\n"
                        "Check the GitHub Actions log."
                    )

            # OTHER
            else:

                send_message(
                    chat_id,
                    "Use /create followed by a niche.\n\n"
                    "Example:\n"
                    "/create science"
                )


if __name__ == "__main__":
    main()
