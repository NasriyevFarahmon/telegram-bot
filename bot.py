import os
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

# Barcha linklar: http(s), t.me, www, va oddiy domain.tld ko‘rinishlari
LINK_RE = re.compile(
    r"("
    r"https?://\S+"
    r"|t\.me/\S+"
    r"|www\.\S+"
    r"|\b[\w-]+\.(?:com|ru|uz|net|org|info|io|me|tv|app|site)\b\S*"
    r")",
    re.IGNORECASE,
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Салом! Ман истинодҳое (линкҳое), ки аз ҷониби ғайриадминҳо фиристода мешаванд ва паёмҳои «даромад/баромад»-ро нест мекунам. Ман боти расмии @DehaiSarchashma мебошам."
    )

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Xabar yuborgan user shu chat adminimi-yo‘qmi tekshiradi."""
    if not update.message:
        return False
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    admins = await context.bot.get_chat_administrators(chat_id)
    return any(a.user.id == user_id for a in admins)

async def delete_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin bo‘lmagan user link yuborsa (text/caption), xabarni o‘chiradi."""
    if not update.message:
        return

    # Admin bo‘lsa tegmaymiz
    if await is_admin(update, context):
        return

    msg = update.message
    text = msg.text or msg.caption or ""
    if not text:
        return

    if LINK_RE.search(text):
        try:
            await msg.delete()
        except Exception:
            pass

async def delete_join_left(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Guruhga kirish/chiqish service message’larini o‘chiradi."""
    if not update.message:
        return
    try:
        await update.message.delete()
    except Exception:
        pass

def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN topilmadi. PowerShell'da $env:BOT_TOKEN='...' qilib ishga tushiring.")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    # Kirdi/chiqdi service messages:
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, delete_join_left))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, delete_join_left))

    # Linklar (oddiy text + media caption):
    app.add_handler(MessageHandler(filters.TEXT | filters.Caption(True), delete_links))

    app.run_polling()

if __name__ == "__main__":
    main()
