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

# Regex (fallback) — entity bo‘lmasa ham linkni ushlash uchun
LINK_RE = re.compile(r"(https?://\S+|www\.\S+|t\.me/\S+|telegram\.me/\S+)", re.IGNORECASE)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Салом! Ман барои нигоҳ доштани тартибот дар гурӯҳ фаъолият мекунам.

Ман боти расмии @DehaiSarchashma мебошам."
        "Вазифаҳои ман:
✅ Истинодҳо (линкҳо)-ро нест мекунам: Агар аз ҷониби ғайриадминҳо фиристода шаванд (дар матн, видео, аудио, акс ва шарҳи файлҳо).

✅ Паёмҳои «даромад/баромад»-ро: Ба таври худкор (автоматӣ) аз гурӯҳ тоза мекунам."
    )
    await update.message.reply_text(text)


async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    admins = await context.bot.get_chat_administrators(chat_id)
    return any(a.user.id == user_id for a in admins)


def has_link(update: Update) -> bool:
    """Text/caption ichida link bormi? (entities + regex)"""
    msg = update.message
    if not msg:
        return False

    # 1) Telegram entities orqali (eng ishonchli)
    entities = (msg.entities or []) + (msg.caption_entities or [])
    if any(e.type in ("url", "text_link") for e in entities):
        return True

    # 2) Regex fallback
    text = msg.text or ""
    caption = msg.caption or ""
    return bool(LINK_RE.search(text) or LINK_RE.search(caption))


async def delete_warning_job(context: ContextTypes.DEFAULT_TYPE):
    """JobQueue orqali ogohlantirish xabarini keyinroq o‘chirish."""
    data = context.job.data
    chat_id = data["chat_id"]
    message_id = data["message_id"]
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass


async def anti_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    # Admin bo‘lsa tegmaymiz
    if await is_admin(update, context):
        return

    # Link bormi?
    if not has_link(update):
        return

    chat_id = update.effective_chat.id
    user = update.effective_user
    mention = user.mention_html()  # HTML mention

    # Avval linkli xabarni o‘chiramiz
    try:
        await update.message.delete()
    except Exception:
        # Delete messages huquqi bo‘lmasa o‘chira olmaydi
        return

    # Ogohlantirish yuboramiz
    warn_text = f"{mention} фиристодани линк манъ аст! Ман боти расмии @DehaiSarchashma мебошам ва паёми шуморо нест кардам."
    warn_msg = await context.bot.send_message(
        chat_id=chat_id,
        text=warn_text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )

    # 10 soniyadan keyin ogohlantirishni ham o‘chirib yuboramiz (spam bo‘lmasin)
    context.job_queue.run_once(
        delete_warning_job,
        when=10,
        data={"chat_id": chat_id, "message_id": warn_msg.message_id},
    )


async def delete_join_leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kirdi/chiqdi service message’larini o‘chiradi."""
    if not update.message:
        return
    try:
        await update.message.delete()
    except Exception:
        pass


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # /start javobi
    app.add_handler(CommandHandler("start", start))

    # Kirdi/chiqdi
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, delete_join_leave))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, delete_join_leave))

    # Anti-link: barcha turdagi xabarlarda tekshiradi (video/audio/photo/doc/caption ham)
    app.add_handler(MessageHandler(filters.ALL, anti_link))

    app.run_polling()


if __name__ == "__main__":
    main()
