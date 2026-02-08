import os
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN topilmadi")

# har qanday linkni aniqlaydi
link_pattern = re.compile(
    r"(https?://|www\.|t\.me/|telegram\.me/)",
    re.IGNORECASE
)

# admin tekshiruv
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    admins = await context.bot.get_chat_administrators(chat_id)
    admin_ids = [admin.user.id for admin in admins]

    return user_id in admin_ids

# link o‘chirish
async def delete_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    if await is_admin(update, context):
        return

    text = update.message.text or ""
    caption = update.message.caption or ""

    if link_pattern.search(text) or link_pattern.search(caption):
        try:
            await update.message.delete()
        except:
            pass

# join/leave o‘chirish
async def delete_join_leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.delete()
    except:
        pass

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # barcha turdagi xabarlar
    app.add_handler(MessageHandler(filters.ALL, delete_links))

    # kirdi/chiqdi
    app.add_handler(MessageHandler(filters.StatusUpdate.ALL, delete_join_leave))

    app.run_polling()

if __name__ == "__main__":
    main()
