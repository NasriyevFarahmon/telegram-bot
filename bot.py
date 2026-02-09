import os
import re
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# Logging sozlamalari
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(name)s", level=logging.INFO)
logger = logging.getLogger("antilink-bot")

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID") # Bot egasining ID raqami

LINK_RE = re.compile(
    r"(https?://|www\.|t\.me/|telegram\.me/|instagr\.am/|instagram\.com/|tiktok\.com/)",
    re.IGNORECASE,
)

# --- Like Tizimi Funksiyalari ---

async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kanalga post tashlanganda like tugmasini qo'shish"""
    channel_post = update.channel_post
    
    # Like tugmasi (boshlang'ich qiymat 0)
    keyboard = [[InlineKeyboardButton("❤️ 0", callback_data="like_0")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await context.bot.edit_message_reply_markup(
            chat_id=channel_post.chat_id,
            message_id=channel_post.message_id,
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Kanal postiga tugma qo'shishda xato: {e}")

async def like_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Like bosilganda hisoblagichni yangilash va adminga xabar yuborish"""
    query = update.callback_query
    data = query.data
    
    if data.startswith("like_"):
        current_likes = int(data.split("_")[1])
        new_likes = current_likes + 1
        
        # Tugmani yangilash
        keyboard = [[InlineKeyboardButton(f"❤️ {new_likes}", callback_data=f"like_{new_likes}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await query.edit_message_reply_markup(reply_markup=reply_markup)
            await query.answer("Rahmat!") # Userga kichik xabar

            # Bot egasiga xabar yuborish
            if ADMIN_ID:
                post_link = f"https://t.me/c/{str(query.message.chat.id)[4:]}/{query.message.message_id}"
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=f"🔔 <b>Yangi Like!</b>\n\nPost: {post_link}\nJami likelar: {new_likes}",
                    parse_mode=ParseMode.HTML
                )
        except Exception as e:
            logger.error(f"Like yangilashda xato: {e}")

# --- Avvalgi Funksiyalar (Anti-link) ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Салом! Ман боти расмии @DehaiSarchashma мебошам.")

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.effective_message.sender_chat or update.effective_chat.type == "private":
            return True
        user_id = update.effective_user.id
        if user_id == 1087968824: return True
        member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
        return member.status in ("administrator", "creator")
    except: return False

async def anti_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or await is_admin(update, context): return

    text = (msg.text or "") + (msg.caption or "")
    if LINK_RE.search(text) or any(e.type in ("url", "text_link") for e in (msg.entities or [])):
        try:
            await msg.delete()
            warn = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Ҳурматӣ {update.effective_user.mention_html()}, линк фиристодан мумкин нест!",
                parse_mode=ParseMode.HTML
            )
            asyncio.create_task(delete_after_delay(warn, 15))
        except: pass

async def delete_after_delay(msg, delay):
    await asyncio.sleep(delay)
    try: await msg.delete()
    except: pass

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(like_callback)) # Like bosilganda
    app.add_handler(MessageHandler(filters.ChatType.CHANNEL, handle_channel_post)) # Kanalda post bo'lganda
    
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND & ~filters.StatusUpdate.ALL, anti_link))

    logger.info("Bot ishga tushdi...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()