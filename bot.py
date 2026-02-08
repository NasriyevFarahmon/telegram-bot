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

LINK_RE = re.compile(r"(https?://|t\.me|www\.)", re.IGNORECASE)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """Салом! Ман боти расмии @DehaiSarchashma мебошам.

Вазифаҳои ман:
- Линкҳоро нест мекунам (аз ғайриадминҳо)
- Паёмҳои даромад/баромадро нест мекунам"""
    await update.message.reply_text(text)


async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    admins = await context.bot.get_chat_administrators(chat_id)
    admin_ids = [a.user.id for a in admins]
    return user_id in admin_ids


async def anti_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    # admin bo‘lsa tegmaymiz
    if await is_admin(update, context):
        return

    msg = update.message
    text = msg.text or ""
    caption = msg.caption or ""

    # ✅ YANGI: entities orqali linkni 100% ushlash (text/caption, video/audio/rasm caption ham)
    entities = (msg.entities or []) + (msg.caption_entities or [])
    has_entity_link = any(e.type in ("url", "text_link") for e in entities)

    # Avval entity tekshiradi, bo‘lmasa regex
    has_link = has_entity_link or LINK_RE.search(text) or LINK_RE.search(caption)

    if has_link:
        user = update.effective_user
        mention = user.mention_html()

        try:
            await update.message.delete()
        except:
            return

        warn = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"{mention} шумо линк фиристодед. Ман боти расмии @DehaiSarchashma мебошам ва паёми шуморо нест кардам.",
            parse_mode=ParseMode.HTML
        )

        # 15 soniyadan keyin warning ham o‘chadi
        await context.application.create_task(delete_later(warn, context))


async def delete_later(msg, context):
    import asyncio
    await asyncio.sleep(15)
    try:
        await context.bot.delete_message(msg.chat_id, msg.message_id)
    except:
        pass


async def delete_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        try:
            await update.message.delete()
        except:
            pass


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    # join leave
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, delete_join))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, delete_join))

    # linklar
    app.add_handler(MessageHandler(
        filters.TEXT | filters.VIDEO | filters.PHOTO | filters.AUDIO | filters.Document.ALL,
        anti_link
    ))

    app.run_polling()


if __name__ == "__main__":
    main()
