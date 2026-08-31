import os
import requests

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
API_URL = f"https://api.telegram.org/bot{TOKEN}"


def send_message(chat_id, text):
    requests.post(
        f"{API_URL}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text
        },
        timeout=30
    )


def main():
    offset = None

    print("SixsContent Bot is running...")

    while True:
        response = requests.get(
            f"{API_URL}/getUpdates",
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

            if text == "/start":
                send_message(
                    chat_id,
                    "🔥 Welcome to SixsContent!\n\n"
                    "Your automated content machine is coming.\n\n"
                    "Phase 1 is working!"
                )

            elif text == "/create":
                send_message(
                    chat_id,
                    "🎬 /create received!\n\n"
                    "Video generation will be connected next."
                )

            else:
                send_message(
                    chat_id,
                    "I received your message: " + text
                )


if __name__ == "__main__":
    main()
