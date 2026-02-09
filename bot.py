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

# --- SOZLAMALAR ---
logging.basicConfig(format="%(asctime)s - %(name)s - %(message)s", level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")  # Bot tokenini muhit o'zgaruvchisidan oladi
ADMIN_ID = 5428723441           # Sizning ID raqamingiz
CHANNEL_ID = -1003117381416      # Kanalingiz ID raqami (raqamli ID oldiga -100 qo'shildi)

# Layklarni xotirada saqlash {message_id: [user_ids]}
likes_data = {}

LINK_RE = re.compile(
    r"(https?://|www\.|t\.me/|telegram\.me/|instagr\.am/|instagram\.com/|tiktok\.com/)",
    re.IGNORECASE,
)

# --- ADMIN PANEL: POST YARATISH ---

async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin botga xabar yuborsa, kanalga yuborish tugmasini ko'rsatadi"""
    if update.effective_user.id != ADMIN_ID:
        return

    keyboard = [[InlineKeyboardButton("✅ Kanalga yuborish", callback_data="send_to_channel")]]
    await update.message.reply_text(
        "📝 Ushbu xabarni kanalga layk tugmasi bilan yuboraymi?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        quote=True
    )
    # Xabarni vaqtinchalik saqlaymiz
    context.user_data['pending_post'] = update.message

async def send_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tugma bosilganda xabarni kanalga yuboradi"""
    query = update.callback_query
    pending_msg = context.user_data.get('pending_post')

    if not pending_msg:
        await query.answer("Xato: Xabar topilmadi. Qaytadan yuboring.", show_alert=True)
        return

    # Boshlang'ich layk tugmasi
    keyboard = [[InlineKeyboardButton("❤️ 0", callback_data="like_0")]]
    
    try:
        # Xabar turiga qarab kanalga yuboramiz (Rasm, Matn, Video va hk)
        sent_msg = await context.bot.copy_message(
            chat_id=CHANNEL_ID,
            from_chat_id=pending_msg.chat_id,
            message_id=pending_msg.message_id,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        # Layk bazasini tayyorlaymiz
        likes_data[sent_msg.message_id] = []
        
        await query.edit_message_text("✅ Xabar kanalga muvaffaqiyatli yuborildi!")
        await query.answer()
    except Exception as e:
        await query.edit_message_text(f"❌ Xatolik: Bot kanalga admin qilinmagan yoki ID xato. \n\nXato matni: {e}")

# --- LAYK BOSISH LOGIKASI ---

async def like_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    msg_id = query.message.message_id
    
    if not query.data.startswith("like_"):
        return

    # Ma'lumotlar bazasini tekshirish
    if msg_id not in likes_data:
        likes_data[msg_id] = []

    # Bitta user bitta layk tekshiruvi
    if user_id in likes_data[msg_id]:
        await query.answer("Siz oldin layk bosgansiz! 😊", show_alert=True)
        return

    # Laykni qo'shish
    likes_data[msg_id].append(user_id)
    count = len(likes_data[msg_id])
    
    # Tugmani yangilash
    keyboard = [[InlineKeyboardButton(f"❤️ {count}", callback_data=f"like_{count}")]]
    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
    await query.answer("Qo'llaganingiz uchun rahmat!")

    # Adminga hisobot yuborish
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📊 <b>Kanaldagi postga yangi layk!</b>\n\nPost ID: {msg_id}\nJami layklar: {count} ta",
        parse_mode=ParseMode.HTML
    )

# --- GURUH UCHUN: ANTI-LINK VA STATUS ---

async def anti_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or update.effective_chat.type == "private": return

    # Admin xabarlariga tegmaymiz
    if msg.sender_chat or (msg.from_user and msg.from_user.id == 1087968824): return
    
    try:
        member = await context.bot.get_chat_member(msg.chat_id, msg.from_user.id)
        if member.status in ("administrator", "creator"): return
    except: pass

    text = (msg.text or "") + (msg.caption or "")
    if LINK_RE.search(text):
        try:
            await msg.delete()
        except: pass

async def delete_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kirdi-chiqdi xabarlarini o'chiradi"""
    try:
        await update.message.delete()
    except: pass

# --- ASOSIY ISHGA TUSHIRISH ---

def main():
    if not TOKEN:
        print("XATO: BOT_TOKEN topilmadi!")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    # Admin boshqaruvi
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, handle_admin_message))
    app.add_handler(CallbackQueryHandler(send_to_channel, pattern="^send_to_channel$"))
    
    # Layk tugmasi qayta ishlagichi
    app.add_handler(CallbackQueryHandler(like_callback, pattern="^like_"))

    # Guruh himoyasi
    app.add_handler(MessageHandler(filters.StatusUpdate.ALL, delete_status))
    app.add_handler(MessageHandler(filters.ChatType.GROUPS & ~filters.COMMAND, anti_link))

    print("Bot ishlamoqda...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()