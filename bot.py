import os
import asyncio
import threading
from flask import Flask
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes
)
from downloader import smart_download

BOT_TOKEN = os.environ.get("BOT_TOKEN")

# ---------- Flask Web Server (UptimeRobot ke liye) ----------
web_app = Flask(__name__)


@web_app.route("/")
@web_app.route("/health")
def health():
    return "OK", 200


def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)


# ---------- Telegram Bot Handlers ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎌 Multi-Site Anime Downloader Bot\n\n"
        "Main in sites ka support karta hoon:\n"
        "• AnimePahe (animepahe.ru)\n"
        "• YouTube aur yt-dlp supported sites\n\n"
        "Bas link bhejo, main download karke bhej dunga."
    )


async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url.startswith("http"):
        await update.message.reply_text("❌ Valid link bhejo (http/https).")
        return

    msg = await update.message.reply_text("⏳ Download shuru ho raha hai...")

    try:
        loop = asyncio.get_event_loop()
        filepath = await loop.run_in_executor(None, smart_download, url)

        if filepath and os.path.exists(filepath):
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            await msg.edit_text(f"📤 Upload ho raha hai... ({size_mb:.1f} MB)")

            with open(filepath, "rb") as f:
                await update.message.reply_video(
                    video=f,
                    caption=f"✅ {os.path.basename(filepath)}",
                    supports_streaming=True,
                    read_timeout=600,
                    write_timeout=600,
                )
            os.remove(filepath)
            await msg.delete()
        else:
            await msg.edit_text(
                "❌ Download fail. Ho sakta hai:\n"
                "• Site ne cookies maangi\n"
                "• Episode link galat hai\n"
                "• Cloudflare block kar raha hai"
            )
    except Exception as e:
        await msg.edit_text(f"⚠️ Error: {str(e)[:300]}")


async def health_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot zinda hai.")


# ---------- Main ----------
def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN env var set karo!")

    # 1. Flask web server ko background daemon thread mein chalao
    web_thread = threading.Thread(target=run_web_server)
    web_thread.daemon = True
    web_thread.start()
    print("🌐 Web server start ho gaya (health check ke liye).")

    # 2. Main thread ke liye naya event loop set karo
    asyncio.set_event_loop(asyncio.new_event_loop())

    # 3. Telegram bot ko main thread mein chalao
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("health", health_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

    print("🤖 Telegram Bot start ho raha hai...")
    app.run_polling(allowed_updates=Update.ALL_TYPES, close_loop=False)


if __name__ == "__main__":
    main()
