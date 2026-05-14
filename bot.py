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
ADMINS = [5428723441, 1375783491] # Bot super-adminlari

LINK_RE = re.compile(r"(https?://|www\.|t\.me/|telegram\.me/|instagr\.am/|instagram\.com/|tiktok\.com/)", re.IGNORECASE)

# Taqiqlangan so'zlar (Hozircha xotirada, keyinchalik bazaga ulash mumkin)
BAD_WORDS = ["haqorat1", "yomon_soz2"] 
likes_data = {}

# --- FUNKSIYALAR ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    is_admin = user.id in ADMINS
    
    if is_admin:
        text = "👋 **Assalomu alaykum, Super-Admin!**\n\nMen barcha admin qilingan guruh va kanallarni nazorat qila olaman.\n\n" \
               "🛠 **Buyruqlar:**\n" \
               "➕ `/add so'z` - Taqiqlangan so'z qo'shish\n" \
               "🚀 Post yuboring - Men unga ❤️ tugmasini qo'shib beraman."
    else:
        text = f"👋 **Salom, {user.first_name}!**\n\n" \
               "🤖 **Men Universal Media va Himoya botiman.**\n\n" \
               "✅ Guruhlarda reklama va haqoratlarni tozalayman.\n" \
               "✅ Kanallarda interaktiv postlar yarataman.\n\n" \
               "ℹ️ Botdan foydalanish uchun uni guruh/kanalingizga admin qiling."

    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# Taqiqlangan so'z qo'shish
async def add_bad_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS: return
    if not context.args:
        await update.message.reply_text("⚠️ Foydalanish: `/add so'z`")
        return
    
    word = context.args[0].lower()
    if word not in BAD_WORDS:
        BAD_WORDS.append(word)
        await update.message.reply_text(f"✅ '{word}' qora ro'yxatga qo'shildi.")
    else:
        await update.message.reply_text("ℹ️ Bu so'z allaqachon mavjud.")

# Guruh va kanallarda xavfsizlik filtri
async def universal_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or update.effective_chat.type == ChatType.PRIVATE: return

    # Adminlar xabarini tekshirmaymiz
    try:
        member = await context.bot.get_chat_member(msg.chat_id, msg.from_user.id)
        if member.status in ["administrator", "creator"]: return
    except: return

    full_content = (msg.text or "") + (msg.caption or "")
    full_content = full_content.lower()

    # 1. Link filtri
    if LINK_RE.search(full_content):
        try:
            await msg.delete()
            warn = await context.bot.send_message(msg.chat_id, f"⚠️ {msg.from_user.mention_markdown()}, guruhda link tarqatish taqiqlangan!")
            await asyncio.sleep(7)
            await warn.delete()
            return
        except: pass

    # 2. Haqoratli so'zlar filtri
    for word in BAD_WORDS:
        if word in full_content:
            try:
                await msg.delete()
                warn = await context.bot.send_message(msg.chat_id, f"⚠️ {msg.from_user.mention_markdown()}, iltimos, odob doirasida muloqot qiling!")
                await asyncio.sleep(7)
                await warn.delete()
                break
            except: pass

# Admin post yuborganda kanal tanlash
async def handle_post_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS: return
    
    context.user_data['temp_post_id'] = update.message.message_id
    context.user_data['temp_from_chat'] = update.message.chat_id
    
    await update.message.reply_text(
        "📝 **Ushbu postga ❤️ tugmasini qo'shib, kanalga yuborishni istaysizmi?**\n\n"
        "Kanal ID-sini yozing yoki pastdagi tugmani bosing.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Ha, yuborish", callback_data="confirm_post")]
        ])
    )

async def confirm_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text("📢 **Post yuboriladigan Kanal ID-sini yuboring.**\n(Masalan: `-100123456789`)")
    context.user_data['waiting_for_cid'] = True

async def get_channel_id_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('waiting_for_cid'): return
    
    target_cid = update.message.text
    post_id = context.user_data.get('temp_post_id')
    from_chat = context.user_data.get('temp_from_chat')
    
    keyboard = [[InlineKeyboardButton("❤️ 0", callback_data=f"like_0")]]
    
    try:
        sent_msg = await context.bot.copy_message(
            chat_id=target_cid,
            from_chat_id=from_chat,
            message_id=post_id,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        likes_data[sent_msg.message_id] = []
        context.user_data['waiting_for_cid'] = False
        await update.message.reply_text("✅ Post kanalga yuborildi!")
    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik: Bot ushbu kanalda admin emas yoki ID noto'g'ri.\n\nError: {e}")

async def like_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    msg = query.message

    if msg.message_id not in likes_data: likes_data[msg.message_id] = []
    
    if user.id in likes_data[msg.message_id]:
        await query.answer("Siz allaqachon ovoz bergansiz! 😊", show_alert=True)
        return

    likes_data[msg.message_id].append(user.id)
    count = len(likes_data[msg.message_id])
    keyboard = [[InlineKeyboardButton(f"❤️ {count}", callback_data=f"like_{count}")]]
    
    try:
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
        await query.answer("Rahmat! Ovoz qabul qilindi.")
    except: pass

async def delete_joins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.message.delete()
    except: pass

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_bad_word))
    
    app.add_handler(CallbackQueryHandler(confirm_post, pattern="confirm_post"))
    app.add_handler(CallbackQueryHandler(like_callback, pattern="^like_"))
    
    app.add_handler(MessageHandler(filters.StatusUpdate.ALL, delete_joins))
    
    # Shaxsiy xabarda post qabul qilish
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND & ~filters.TEXT, handle_post_request))
    # Kanal ID kutish
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, get_channel_id_and_send))
    
    # Guruhlar va Kanallar uchun filtr
    app.add_handler(MessageHandler((filters.ChatType.GROUPS | filters.ChatType.CHANNEL) & ~filters.COMMAND, universal_filter))
    
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
