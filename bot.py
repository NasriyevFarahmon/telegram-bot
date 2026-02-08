import os
import re
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

# Tokenni muhit o'zgaruvchisidan olish
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN topilmadi")

# Linklarni aniqlash uchun Regex
LINK_RE = re.compile(r"(https?://|t\.me|www\.)", re.IGNORECASE)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """Салом! Ман боти расмии @DehaiSarchashma мебошам.

Вазифаҳои ман:
- Линкҳоро (матн, расм, видео ва ғ.) нест мекунам
- Паёмҳои даромад/баромадро нест мекунам"""
    await update.message.reply_text(text)

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        # Shaxsiy chatlarda admin tekshiruvi kerak emas
        if update.effective_chat.type == "private":
            return True
            
        admins = await context.bot.get_chat_administrators(chat_id)
        return any(a.user.id == user_id for a in admins)
    except:
        return False

async def anti_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    # Admin bo‘lsa e'tibor bermaymiz
    if await is_admin(update, context):
        return

    msg = update.message
    text = msg.text or ""
    caption = msg.caption or ""

    # Linklarni aniqlash (ham oddiy matn, ham media izohi ichidan)
    entities = (msg.entities or []) + (msg.caption_entities or [])
    has_entity_link = any(e.type in ("url", "text_link") for e in entities)
    
    # Agar matnda yoki izohda link bo'lsa
    if has_entity_link or LINK_RE.search(text) or LINK_RE.search(caption):
        user = update.effective_user
        mention = user.mention_html()

        try:
            await msg.delete()
        except Exception as e:
            print(f"Xatolik o'chirishda: {e}")
            return

        warn = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"{mention} шумо линк фиристодед. Ман боти расмии @DehaiSarchashma мебошам ва паёми шуморо нест кардам.",
            parse_mode=ParseMode.HTML
        )

        # 15 soniyadan keyin ogohlantirishni o'chirish
        context.application.create_task(delete_later(warn, context))

async def delete_later(msg, context):
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

    # Guruhga qo'shilganlar va chiqib ketganlar haqidagi xabarlarni o'chirish
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, delete_join))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, delete_join))

    # Barcha turdagi xabarlarni (Matn, Rasm, Video, Audio, Hujjat, Voice) link bor-yo'qligiga tekshirish
    all_media_filter = (
        filters.TEXT | 
        filters.PHOTO | 
        filters.VIDEO | 
        filters.AUDIO | 
        filters.VOICE | 
        filters.Document.ALL | 
        filters.VIDEO_NOTE
    )
    
    app.add_handler(MessageHandler(all_media_filter, anti_link))

    print("Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()