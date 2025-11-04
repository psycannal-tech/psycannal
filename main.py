import os
import logging
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# ===== логування =====
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== змінні середовища =====
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# якщо немає токена — одразу показати в логах
if not TELEGRAM_TOKEN:
    logger.error("❌ TELEGRAM_TOKEN не заданий у змінних середовища!")
if not OPENAI_API_KEY:
    logger.warning("⚠️ OPENAI_API_KEY не заданий — бот відповідатиме без ШІ")

client = None
if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)

# ===== Telegram-логіка =====
WELCOME = (
    "Привіт 🌿 Я Harmonia.\n"
    "Напиши, що турбує — я відповім.\n"
    "Або введи /vprava, щоб отримати психо-вправу."
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME)

async def vprava(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🧘 Вправа «4-7-8»:\n"
        "1) вдих на 4\n"
        "2) затримка на 7\n"
        "3) видих на 8\n"
        "Повтори 4 кола."
    )

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    # якщо нема ключа openai – відповідаємо простим текстом
    if client is None:
        await update.message.reply_text("Я поки без ШІ, але я тут 🙂 Напиши /vprava.")
        return

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ти доброзичливий психологічний асистент українською."},
                {"role": "user", "content": user_text},
            ],
        )
        answer = resp.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        answer = "Схоже, в мене зараз технічна пауза 🤖 Спробуй трохи пізніше."
    await update.message.reply_text(answer)


def make_telegram_app() -> Application:
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("vprava", vprava))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    return app

# ===== Flask, щоб Render бачив, що ми живі =====
flask_app = Flask(__name__)

@flask_app.get("/")
def home():
    return "Harmonia bot is running ✅"

async def run_telegram(app: Application):
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    logger.info("🤖 Telegram bot started (polling)")

def main():
    tg_app = make_telegram_app()

    import asyncio
    loop = asyncio.get_event_loop()
    loop.create_task(run_telegram(tg_app))

    port = int(os.getenv("PORT", 8000))
    flask_app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
