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

from telethon import TelegramClient
from telethon.sessions import StringSession


TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

TELEGRAM_API_ID = int(os.environ["TELEGRAM_API_ID"])
TELEGRAM_API_HASH = os.environ["TELEGRAM_API_HASH"]
TELEGRAM_SESSION = os.environ.get("TELEGRAM_SESSION", "")


client = AsyncOpenAI(api_key=OPENAI_API_KEY)

user_client = TelegramClient(
    StringSession(TELEGRAM_SESSION),
    TELEGRAM_API_ID,
    TELEGRAM_API_HASH,
)


SYSTEM_PROMPT = """
Sen foydalanuvchilarga Telegram orqali yordam beradigan aqlli AI yordamchisan.

Javoblarni o'zbek tilida ber.
Savol tushunarsiz bo'lsa, aniqlashtiruvchi savol ber.
Javoblarni qisqa, tushunarli va foydali qil.
"""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Assalomu alaykum! 👋\n"
        "Men AI yordamchiman.\n\n"
        "Shaxsiy Telegram akkauntingizni ulash uchun /connect buyrug'ini yuboring."
    )


async def connect_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not user_client.is_connected():
            await user_client.connect()

        if await user_client.is_user_authorized():
            await update.message.reply_text(
                "✅ Shaxsiy Telegram akkauntingiz allaqachon ulangan."
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
                "📱 Telegram akkauntingizni ulash uchun:\n\n"
                "1. Telegram → Settings\n"
                "2. Devices\n"
                "3. Link Desktop Device\n"
                "4. Shu QR kodni skanerlang.\n\n"
                "QR kodni skanerlagandan keyin kuting..."
            ),
        )

        await qr_login.wait()

        session_string = user_client.session.save()

        print("\n" + "=" * 60)
        print("TELEGRAM_SESSION:")
        print(session_string)
        print("=" * 60 + "\n")

        await update.message.reply_text(
            "✅ Telegram akkauntingiz muvaffaqiyatli ulandi!\n\n"
            "Endi Railway'ga session ma'lumotini saqlash kerak."
        )

    except Exception as e:
        print(f"CONNECT ERROR: {e}")
        await update.message.reply_text(
            "❌ Ulanishda xatolik yuz berdi.\n"
            "Railway loglarini tekshirish kerak."
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_text = update.message.text

    try:
        response = await client.responses.create(
            model="gpt-5.5",
            instructions=SYSTEM_PROMPT,
            input=user_text,
        )

        answer = response.output_text

        await update.message.reply_text(answer)

    except Exception as e:
        print(f"ERROR: {e}")
        await update.message.reply_text(
            "Kechirasiz, hozir texnik xatolik yuz berdi. "
            "Birozdan keyin qayta urinib ko'ring."
        )


def main():
    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("connect", connect_telegram))

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    application.run_polling()


if __name__ == "__main__":
    main()
