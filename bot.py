import os
import re
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN topilmadi")

# Kuchliroq fallback regex:
# - https://...
# - www....
# - t.me/...
# - telegram.me/...
# - domain.tld/... (instagram.com, google.com, bit.ly, va h.k.)
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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """Салом! Ман боти расмии @DehaiSarchashma мебошам.

Вазифаҳои ман:
- Линкҳоро нест мекунам (аз ғайриадминҳо)
- Паёмҳои даромад/баромадро нест мекунам"""
    await update.message.reply_text(text)


async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
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
    """15 soniyadan keyin ogohlantirishni o‘chiradi."""
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

    # admin bo‘lsa tegmaymiz
    if await is_admin(update, context):
        return

    if not has_link(msg):
        return

    user = update.effective_user
    mention = user.mention_html()

    # Linkli xabarni o‘chir
    try:
        await msg.delete()
    except Exception:
        return

    # Ogohlantirish yubor
    warn_msg = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"{mention} шумо линк фиристодед. Ман боти расмии @DehaiSarchashma мебошам ва паёми шуморо нест кардам.",
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )

    # 15 soniyadan keyin warning ham o‘chadi (JobQueue barqarorroq)
    context.job_queue.run_once(
        delete_warning_job,
        when=15,
        data={"chat_id": warn_msg.chat_id, "message_id": warn_msg.message_id},
    )


async def delete_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        try:
            await update.message.delete()
        except Exception:
            pass


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    # join/leave
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, delete_join))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, delete_join))

    # ✅ MUHIM: hamma xabar turlari, lekin status update va command emas
    app.add_handler(MessageHandler(filters.ALL & ~filters.StatusUpdate.ALL & ~filters.COMMAND, anti_link))

    app.run_polling()


if __name__ == "__main__":
    main()
