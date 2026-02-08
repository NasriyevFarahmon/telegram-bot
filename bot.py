import os
import re
import logging
import asyncio
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Logging sozlamalari (Railway loglarida ko'rish uchun)
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("antilink-bot")

TOKEN = os.getenv("BOT_TOKEN")

# Linklar uchun regex
LINK_RE = re.compile(
    r"(https?://|www\.|t\.me/|telegram\.me/|instagr\.am/|instagram\.com/|tiktok\.com/)",
    re.IGNORECASE,
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Салом! Ман барои нигоҳ доштани тартибот дар гурӯҳ фаъолият мекунам.Ман боти расмии @DehaiSarchashma мебошам.")

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.effective_chat.type == "private":
            return True
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("administrator", "creator")
    except Exception as e:
        logger.error(f"Admin tekshirishda xato: {e}")
        return False

def get_entities(msg):
    """Xatoni oldini olish uchun entitiesni list ko'rinishida yig'ish."""
    all_entities = []
    if msg.entities:
        all_entities.extend(list(msg.entities))
    if msg.caption_entities:
        all_entities.extend(list(msg.caption_entities))
    return all_entities

async def anti_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    # Admin bo'lsa tekshirmaymiz
    if await is_admin(update, context):
        return

    # Linklarni tekshirish (Logingizdagi xato shu yerda tuzatildi)
    entities = get_entities(msg)
    has_hidden_link = any(e.type in ("url", "text_link") for e in entities)
    
    text = msg.text or ""
    caption = msg.caption or ""
    has_regex_link = LINK_RE.search(text) or LINK_RE.search(caption)

    if has_hidden_link or has_regex_link:
        try:
            await msg.delete()
            user = update.effective_user.mention_html()
            warn = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"{user}, фиристодани линк манъ аст! Ман боти расмии @DehaiSarchashma мебошам ва паёми шуморо нест кардам!",
                parse_mode=ParseMode.HTML
            )
            # Ogohlantirishni 15 soniyadan keyin o'chirish
            asyncio.create_task(delete_after_delay(warn, 15))
            logger.info(f"Link o'chirildi: User ID {update.effective_user.id}")
        except Exception as e:
            logger.error(f"Xabarni o'chirishda xatolik: {e}")

async def delete_after_delay(msg, delay):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except:
        pass

async def delete_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kirdi-chiqdi xabarlarini o'chiradi."""
    try:
        await update.message.delete()
    except:
        pass

def main():
    if not TOKEN:
        logger.error("BOT_TOKEN topilmadi!")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.ALL, delete_status))
    
    # Barcha media va matnlarni tekshirish (Linklar uchun)
    app.add_handler(MessageHandler(
        filters.ALL & ~filters.COMMAND & ~filters.StatusUpdate.ALL, 
        anti_link
    ))

    logger.info("Bot polling boshladi...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()