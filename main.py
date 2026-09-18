import os

from openai import AsyncOpenAI
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

client = AsyncOpenAI(api_key=OPENAI_API_KEY)


SYSTEM_PROMPT = """
Sen foydalanuvchilarga Telegram orqali yordam beradigan aqlli AI yordamchisan.

Javoblarni o'zbek tilida ber.
Savol tushunarsiz bo'lsa, aniqlashtiruvchi savol ber.
Javoblarni qisqa, tushunarli va foydali qil.
Hozircha o'zingni oddiy AI yordamchi sifatida tut.
"""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Assalomu alaykum! 👋\n"
        "Men AI yordamchiman. Savolingizni yozing."
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
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    application.run_polling()


if __name__ == "__main__":
    main()
