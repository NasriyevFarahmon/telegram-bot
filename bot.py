import os
import re
import asyncio
import logging
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# === Logs (Railway Logs'da ko'rinadi) ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("antilink-bot")

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN topilmadi")

# Kuchliroq Regex: Instagram, TikTok, Telegram va umumiy linklar uchun
LINK_RE = re.compile(r"(https?://|t\.me|www\.|instagr\.am|instagram\.com|tiktok\.com)", re.IGNORECASE)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот фаол! Гуруҳдаги линк ва рекламаларни тозалайман.")

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        return True
    try:
        member = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
        return member.status in ("administrator", "creator")
    except:
        return False

async def anti_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Agar xabar guruhdan bo'lmasa yoki xabar bo'lmasa to'xtatamiz
    if not update.message:
        return

    # Adminlarni tekshirish (Admin yuborgan link o'chmaydi)
    if await is_admin(update, context):
        return

    msg = update.message
    text = msg.text or ""
    caption = msg.caption or ""

    # 1. Ko'rinmas linklarni (Hyperlinks) aniqlash
    entities = (msg.entities or []) + (msg.caption_entities or [])
    has_hidden_link = any(e.type in ("url", "text_link") for e in entities)

    # 2. Matn ichidagi oddiy linklarni aniqlash
    has_regex_link = LINK_RE.search(text) or LINK_RE.search(caption)

    if has_hidden_link or has_regex_link:
        try:
            await msg.delete()
            
            user = update.effective_user.mention_html()
            warn = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"{user}, гуруҳда линк тарқатиш тақиқланган!",
                parse_mode=ParseMode.HTML
            )
            # 15 soniyadan keyin ogohlantirishni o'chirish
            context.application.create_task(delete_later(warn, context))
            logger.info(f"Link o'chirildi: User: {update.effective_user.id}")
        except Exception as e:
            logger.error(f"Xabar o'chirishda xatolik: {e}")

async def delete_later(msg, context):
    await asyncio.sleep(15)
    try:
        await context.bot.delete_message(msg.chat_id, msg.message_id)
    except:
        pass

async def delete_status_updates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Guruhga kirdi-chiqdi xabarlarini o'chiradi"""
    try:
        await update.message.delete()
    except:
        pass

def main():
    # Botni yaratish
    app = ApplicationBuilder().token(TOKEN).build()

    # Buyruqlar
    app.add_handler(CommandHandler("start", start))

    # Kirdi-chiqdi xabarlarini o'chirish
    app.add_handler(MessageHandler(filters.StatusUpdate.ALL, delete_status_updates))

    # ASOSIY: Barcha turdagi xabarlardan link qidirish (Rasm, Video, Audio, Hujjat, Matn)
    # filters.ALL ishlatamiz, shunda hamma narsani tekshiradi
    app.add_handler(MessageHandler(
        (filters.TEXT | filters.PHOTO | filters.VIDEO | filters.AUDIO | filters.VOICE | filters.Document.ALL | filters.VIDEO_NOTE) & (~filters.COMMAND), 
        anti_link
    ))

    logger.info("Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()