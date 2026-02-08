import os
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN topilmadi")

# HAR QANDAY LINK
LINK_RE = re.compile(
    r"(https?://\S+|www\.\S+|t\.me/\S+)",
    re.IGNORECASE
)

# ADMIN TEKSHIRUV
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    admins = await context.bot.get_chat_administrators(chat_id)
    admin_ids = [a.user.id for a in admins]

    return user_id in admin_ids

# LINK O‘CHIRISH
async def anti_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    if await is_admin(update, context):
        return

    text = update.message.text or ""
    caption = update.message.caption or ""

    if LINK_RE.search(text) or LINK_RE.search(caption):
        try:
            await update.message.delete()
        except:
            pass

# KIRDI/CHIQDI O‘CHIRISH
async def delete_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.delete()
    except:
        pass

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # BARCHA XABARLAR (video/audio ham)
    app.add_handler(MessageHandler(filters.ALL, anti_link))

    # JOIN/LEAVE
    app.add_handler(MessageHandler(filters.StatusUpdate.ALL, delete_service))

    app.run_polling()

if __name__ == "__main__":
    main()
