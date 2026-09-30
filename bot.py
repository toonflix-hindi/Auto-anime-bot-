import os
import asyncio
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes
)
from downloader import smart_download

BOT_TOKEN = os.environ.get("BOT_TOKEN")


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


async def health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot zinda hai.")


def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN env var set karo!")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("health", health))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    print("🤖 Bot start ho raha hai...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()