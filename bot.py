import os
import re
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

# ===== Logs (Railway Logs'da ko‘rinadi) =====
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("antilink-bot")

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN topilmadi")

# Kuchliroq fallback regex (entities bo‘lmasa ham ushlaydi)
LINK_RE = re.compile(
    r"("
    r"https?://\S+"
    r"|www\.\S+"
    r"|t\.me/\S+"
    r"|telegram\.me/\S+"
    r"|\b[a-z0-9-]+\.(?:com|ru|uz|net|org|info|io|me|tv|app|site|xyz)\b\S*"
    r")",
    re.IGNORECASE,
)

START_TEXT = """Салом! Ман боти расмии @DehaiSarchashma мебошам.

Вазифаҳои ман:
✅ Аз ғайриадминҳо фиристода шудани ҳама гуна линкҳоро нест мекунам (матн, видео, аудио, акс, ҳуҷҷат, voice, GIF — ҳатто дар caption).
✅ Паёмҳои «даромад/баромад»-ро автоматӣ нест мекунам.
"""

WARN_TEXT = "шумо линк фиристодед. Ман боти расмии @DehaiSarchashma мебошам ва паёми шуморо нест кардам."


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(START_TEXT)


async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    admins = await context.bot.get_chat_administrators(chat_id)
    return any(a.user.id == user_id for a in admins)


def has_link(msg) -> bool:
    """Entities + regex fallback bilan linkni aniqlaydi (text/caption)."""
    if not msg:
        return False

    entities = (msg.entities or []) + (msg.caption_entities or [])
    if any(e.type in ("url", "text_link") for e in entities):
        return True

    text = msg.text or ""
    caption = msg.caption or ""
    return bool(LINK_RE.search(text) or LINK_RE.search(caption))


async def delete_warning_job(context: ContextTypes.DEFAULT_TYPE):
    data = context.job.data
    try:
        await context.bot.delete_message(chat_id=data["chat_id"], message_id=data["message_id"])
    except Exception:
        pass


async def anti_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    # Buyruqlarni tekshirmaymiz
    if msg.text and msg.text.startswith("/"):
        return

    # Admin bo‘lsa tegmaymiz
    try:
        if await is_admin(update, context):
            return
    except Exception as e:
        logger.exception("Admin check error: %s", e)
        return

    # Link bo‘lmasa tegmaymiz
    if not has_link(msg):
        return

    chat_id = update.effective_chat.id
    user = update.effective_user
    mention = user.mention_html()

    # Linkli xabarni o‘chiramiz
    try:
        await msg.delete()
        logger.info("Deleted link message in chat_id=%s from user_id=%s", chat_id, user.id)
    except Exception as e:
        logger.exception("FAILED to delete message in chat_id=%s: %s", chat_id, e)
        return

    # Ogohlantirish yuboramiz
    warn_msg = await context.bot.send_message(
        chat_id=chat_id,
        text=f"{mention} {WARN_TEXT}",
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )

    # 15 soniyadan keyin warning ham o‘chadi
    context.job_queue.run_once(
        delete_warning_job,
        when=15,
        data={"chat_id": warn_msg.chat_id, "message_id": warn_msg.message_id},
    )


async def delete_join_leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kirdi/chiqdi service message’larini o‘chiradi."""
    msg = update.message
    if not msg:
        return
    try:
        await msg.delete()
    except Exception:
        pass


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # /start
    app.add_handler(CommandHandler("start", start))

    # join/leave
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, delete_join_leave))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, delete_join_leave))

    # ✅ hamma xabar turlari (video/audio/photo/doc/voice/gif ham),
    # lekin status update va command emas
    app.add_handler(MessageHandler(filters.ALL & ~filters.StatusUpdate.ALL & ~filters.COMMAND, anti_link))

    logger.info("Bot started. Polling...")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
