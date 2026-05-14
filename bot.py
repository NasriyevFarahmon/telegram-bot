import os
import re
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode, ChatType
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# Logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# --- KONFIGURATSIYA ---
TOKEN = os.getenv("BOT_TOKEN")
ADMINS = [5428723441, 1375783491] 

LINK_RE = re.compile(r"(https?://|www\.|t\.me/|telegram\.me/|instagr\.am/|instagram\.com/|tiktok\.com/)", re.IGNORECASE)

# Taqiqlangan so'zlar
BAD_WORDS = ["haqorat1", "yomon_soz2"] 
likes_data = {}

# --- FUNKSIYALAR ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id in ADMINS:
        text = "👋 **Assalomu alaykum, Admin!**\n\nMen universal himoya botiman.\n\n" \
               "➕ `/add so'z` - Taqiqlangan so'z qo'shish\n" \
               "🚀 Istalgan xabarni (rasm, tekst) menga yuboring, men unga tugma qo'shib beraman."
    else:
        text = "👋 **Salom!** Men guruh va kanallarni himoya qiluvchi universal botman.\n" \
               "Meni guruhga admin qilsangiz, link va haqoratlarni o'chiraman."
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def add_bad_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS: return
    if not context.args:
        await update.message.reply_text("⚠️ Misol: `/add yomon_soz`")
        return
    word = context.args[0].lower()
    if word not in BAD_WORDS:
        BAD_WORDS.append(word)
        await update.message.reply_text(f"✅ '{word}' ro'yxatga qo'shildi.")

async def universal_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Guruhlarda link va haqoratni o'chirish"""
    msg = update.message
    if not msg or msg.chat.type == ChatType.PRIVATE: return

    # Adminlarni tekshirmaslik
    try:
        member = await context.bot.get_chat_member(msg.chat_id, msg.from_user.id)
        if member.status in ["administrator", "creator"]: return
    except: return

    full_text = (msg.text or "") + (msg.caption or "")
    full_text = full_text.lower()

    if LINK_RE.search(full_text) or any(word in full_text for word in BAD_WORDS):
        try:
            await msg.delete()
        except Exception as e:
            logging.error(f"O'chirishda xatolik: {e}")

async def handle_media_for_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin yuborgan xabarni ushlab qolish"""
    if update.effective_user.id not in ADMINS: return
    if update.message.chat.type != ChatType.PRIVATE: return

    context.user_data['post_msg_id'] = update.message.message_id
    
    await update.message.reply_text(
        "📝 **Post tayyor!**\n\nEndi ushbu postni yubormoqchi bo'lgan Kanal ID-sini yuboring.\n"
        "Masalan: `-100123456789`",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel")]])
    )
    context.user_data['waiting_for_id'] = True

async def receive_channel_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kanal ID-sini qabul qilish va postni yuborish"""
    if not context.user_data.get('waiting_for_id'):
        # Agar admin shunchaki tekst yozsa va post kutmayotgan bo'lsak, startga qaytaramiz
        return

    channel_id = update.message.text
    post_id = context.user_data.get('post_msg_id')

    keyboard = [[InlineKeyboardButton("❤️ 0", callback_data="like_action")]]

    try:
        # Kanalga nusxasini yuborish
        await context.bot.copy_message(
            chat_id=channel_id,
            from_chat_id=update.effective_chat.id,
            message_id=post_id,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        await update.message.reply_text("✅ Kanalga muvaffaqiyatli yuborildi!")
        context.user_data['waiting_for_id'] = False
    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik! Kanal ID noto'g'ri yoki bot u yerda admin emas.\n\n`{e}`", parse_mode=ParseMode.MARKDOWN)

async def like_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    msg_id = query.message.message_id

    if msg_id not in likes_data: likes_data[msg_id] = set()

    if user_id in likes_data[msg_id]:
        await query.answer("Siz allaqachon ovoz bergansiz! 😊", show_alert=True)
    else:
        likes_data[msg_id].add(user_id)
        count = len(likes_data[msg_id])
        keyboard = [[InlineKeyboardButton(f"❤️ {count}", callback_data="like_action")]]
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
        await query.answer("Rahmat!")

def main():
    if not TOKEN:
        print("Xatolik: BOT_TOKEN topilmadi!")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_bad_word))
    app.add_handler(CallbackQueryHandler(like_button_click, pattern="like_action"))
    
    # 1. Shaxsiy xabarda media/tekst (Post uchun)
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND & (filters.ALL & ~filters.TEXT), handle_media_for_post))
    
    # 2. Shaxsiy xabarda Kanal ID kutish (faqat kutayotgan bo'lsa)
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, receive_channel_id))

    # 3. Guruh va Kanallarda filtr
    app.add_handler(MessageHandler((filters.ChatType.GROUPS | filters.ChatType.CHANNEL) & ~filters.COMMAND, universal_filter))

    print("Bot ishga tushdi...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
