import os
from io import BytesIO

import qrcode
from openai import AsyncOpenAI

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError


TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

TELEGRAM_API_ID = int(os.environ["TELEGRAM_API_ID"])
TELEGRAM_API_HASH = os.environ["TELEGRAM_API_HASH"]

TELEGRAM_SESSION = os.environ.get("TELEGRAM_SESSION", "")
TELEGRAM_2FA_PASSWORD = os.environ.get("TELEGRAM_2FA_PASSWORD", "")


openai_client = AsyncOpenAI(
    api_key=OPENAI_API_KEY
)


user_client = TelegramClient(
    StringSession(TELEGRAM_SESSION),
    TELEGRAM_API_ID,
    TELEGRAM_API_HASH,
)


SYSTEM_PROMPT = """
Sen aqlli AI yordamchisan.

Javoblarni o'zbek tilida ber.
Savol tushunarsiz bo'lsa, aniqlashtiruvchi savol ber.
Javoblarni foydali, tushunarli va tabiiy yoz.
"""


async def ask_ai(text):
    response = await openai_client.responses.create(
        model="gpt-5.5",
        instructions=SYSTEM_PROMPT,
        input=text,
    )

    return response.output_text


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Assalomu alaykum! 👋\n\n"
        "Men AI yordamchiman.\n\n"
        "/connect — shaxsiy Telegram akkauntini ulash"
    )


async def connect_telegram(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    try:
        if not user_client.is_connected():
            await user_client.connect()

        if await user_client.is_user_authorized():
            user_client.add_event_handler(
                handle_personal_message,
                events.NewMessage(incoming=True)
            )

            await update.message.reply_text(
                "✅ Shaxsiy Telegram akkauntingiz ulangan!"
            )
            return

        qr_login = await user_client.qr_login()

        qr_image = qrcode.make(qr_login.url)

        image_bytes = BytesIO()
        qr_image.save(image_bytes, format="PNG")
        image_bytes.seek(0)

        await update.message.reply_photo(
            photo=image_bytes,
            caption=(
                "📱 Telegram akkauntingizni ulash:\n\n"
                "1. Telegram → Settings\n"
                "2. Devices\n"
                "3. Link Desktop Device\n"
                "4. Shu QR kodni skanerlang.\n\n"
                "Skanerlagandan keyin kuting..."
            ),
        )

        try:
            await qr_login.wait()

        except SessionPasswordNeededError:

            if not TELEGRAM_2FA_PASSWORD:
                await update.message.reply_text(
                    "❌ Telegram 2FA paroli topilmadi."
                )
                return

            await user_client.sign_in(
                password=TELEGRAM_2FA_PASSWORD
            )

        if await user_client.is_user_authorized():

            user_client.add_event_handler(
                handle_personal_message,
                events.NewMessage(incoming=True)
            )

            await update.message.reply_text(
                "✅ Telegram akkauntingiz muvaffaqiyatli ulandi!\n\n"
                "Endi shaxsiy Telegram akkauntingizga yozilgan "
                "xabarlarni AI o'qib javob beradi."
            )

    except Exception as e:
        print(f"CONNECT ERROR: {e}")

        await update.message.reply_text(
            "❌ Ulanishda xatolik yuz berdi."
        )


async def handle_bot_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not update.message:
        return

    if not update.message.text:
        return

    try:
        answer = await ask_ai(update.message.text)

        await update.message.reply_text(answer)

    except Exception as e:
        print(f"BOT ERROR: {e}")

        await update.message.reply_text(
            "Kechirasiz, texnik xatolik yuz berdi."
        )


async def handle_personal_message(event):
    try:
        if not event.is_private:
            return

        if event.out:
            return

        text = event.raw_text.strip()

        if not text:
            return

        print("📩 Personal Telegram xabari keldi")

        answer = await ask_ai(text)

        await event.respond(answer)

        print("✅ Personal Telegram javobi yuborildi")

    except Exception as e:
        print(f"PERSONAL TELEGRAM ERROR: {e}")


async def post_init(application):
    try:
        if not user_client.is_connected():
            await user_client.connect()

        if await user_client.is_user_authorized():

            user_client.add_event_handler(
                handle_personal_message,
                events.NewMessage(incoming=True)
            )

            print("✅ PERSONAL TELEGRAM LISTENER: ACTIVE")

        else:
            print("⚠️ PERSONAL TELEGRAM: NOT AUTHORIZED")

    except Exception as e:
        print(f"TELEGRAM START ERROR: {e}")


async def post_shutdown(application):
    try:
        if user_client.is_connected():
            await user_client.disconnect()

    except Exception as e:
        print(f"TELEGRAM SHUTDOWN ERROR: {e}")


def main():

    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("connect", connect_telegram)
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_bot_message
        )
    )

    application.run_polling()


if __name__ == "__main__":
    main()
