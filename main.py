import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from openai import OpenAI

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# клієнт OpenAI без всяких proxies — це було джерело помилки минулого разу
client = OpenAI(api_key=OPENAI_API_KEY)


# ---------------- команді бота ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Привіт 🌿 Я Гармонія.\n"
        "Можу дати вправу — /vprava\n"
        "А можу просто підтримати — напиши, що турбує 💬"
    )
    await update.message.reply_text(text)


async def vprava(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🌸 Вправа на заземлення:\n"
        "1. Назви 5 предметів, які бачиш.\n"
        "2. 4 звуки, які чуєш.\n"
        "3. 3 дотики, які відчуваєш.\n"
        "4. 2 запахи.\n"
        "5. 1 приємну думку 💚"
    )
    await update.message.reply_text(text)


# ---------------- чат через OpenAI ----------------
async def chat_with_ai(user_text: str) -> str:
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ти емпатичний україномовний психологічний асистент. "
                        "Відповідай коротко, підтримуюче, без медичних діагнозів."
                    ),
                },
                {"role": "user", "content": user_text},
            ],
            max_tokens=300,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        return "Схоже, в мене технічна пауза 😔 Спробуй ще раз трохи пізніше."


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    reply = await chat_with_ai(user_text)
    await update.message.reply_text(reply)


async def main():
    if not TELEGRAM_TOKEN:
        raise RuntimeError("TELEGRAM_TOKEN не заданий в environment variables")
    if not OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY не заданий — відповіді ШІ не працюватимуть")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("vprava", vprava))
    # усе інше — в ШІ
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("Bot is running (polling)...")
    await app.run_polling(stop_signals=None)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
