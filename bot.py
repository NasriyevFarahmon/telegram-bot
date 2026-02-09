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

# Sozlamalar
logging.basicConfig(format="%(asctime)s - %(name)s - %(message)s", level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0")) # Bot egasining ID si
CHANNEL_ID = "@SizningKanalUseri" # Kanal usernamesi yoki ID si

# Ma'lumotlarni saqlash (Vaqtinchalik bazacha)
# {message_id: [user_id1, user_id2]} ko'rinishida saqlaydi
likes_data = {}

LINK_RE = re.compile(r"(https?://|www\.|t\.me/|telegram\.me/|instagr\.am/|instagram\.com/|tiktok\.com/)", re.IGNORECASE)

# --- POST YARATISH (ADMIN UCHUN) ---

async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin botga biror narsa yozsa, uni kanalga yuborish variantini taklif qiladi"""
    if update.effective_user.id != ADMIN_ID:
        return # Admin bo'lmasa e'tiborsiz qoldiramiz

    if update.message.text or update.message.caption:
        keyboard = [[InlineKeyboardButton("✅ Kanalga yuborish", callback_data="send_to_channel")]]
        await update.message.reply_text(
            "Ushbu xabarni kanalga layk tugmasi bilan yubormoqchimisiz?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        # Xabarni keyinroq yuborish uchun contextda saqlab turamiz
        context.user_data['pending_post'] = update.message

async def send_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin 'Yubor' tugmasini bossa, xabarni kanalga chiqaradi"""
    query = update.callback_query
    pending_msg = context.user_data.get('pending_post')

    if not pending_msg:
        await query.answer("Xabar topilmadi, qaytadan yuboring.")
        return

    # Layk tugmasi bilan kanalga yuborish
    keyboard = [[InlineKeyboardButton("❤️ 0", callback_data="like_0")]]
    
    try:
        if pending_msg.text:
            sent_msg = await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=pending_msg.text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            sent_msg = await context.bot.copy_message(
                chat_id=CHANNEL_ID,
                from_chat_id=pending_msg.chat_id,
                message_id=pending_msg.message_id,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        likes_data[sent_msg.message_id] = [] # Bu post uchun bo'sh ro'yxat ochamiz
        await query.edit_message_text("✅ Xabar kanalga muvaffaqiyatli yuborildi!")
    except Exception as e:
        await query.edit_message_text(f"❌ Xatolik yuz berdi: {e}")

# --- LAYK BOSISH LOGIKASI ---

async def like_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    msg_id = query.message.message_id
    data = query.data

    if not data.startswith("like_"):
        return

    # Post uchun layk ro'yxatini tekshirish
    if msg_id not in likes_data:
        likes_data[msg_id] = []

    if user_id in likes_data[msg_id]:
        await query.answer("Siz oldin layk bosgansiz!", show_alert=True)
        return

    # Yangi laykni qayd etish
    likes_data[msg_id].append(user_id)
    count = len(likes_data[msg_id])
    
    keyboard = [[InlineKeyboardButton(f"❤️ {count}", callback_data=f"like_{count}")]]
    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
    await query.answer("Qo'llaganingiz uchun rahmat!")

    # Adminga doimiy xabar
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📊 Post #{msg_id} da yangi layk!\nJami: {count} ta"
    )

# --- ANTI-LINK VA STATUS O'CHIRISH (GURUH UCHUN) ---

async def anti_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or update.effective_chat.type == "private": return

    # Adminlarni tekshirish
    if msg.sender_chat: return # Kanal nomidan kelgan xabar
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
    """Guruhga kirdi-chiqdi xabarlarini o'chirish"""
    try:
        await update.message.delete()
    except:
        pass

# --- ASOSIY QISM ---

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Admin xabarlarini ushlash (Faqat shaxsiyda)
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, handle_admin_message))
    app.add_handler(CallbackQueryHandler(send_to_channel, pattern="^send_to_channel$"))
    
    # Layk tugmasi
    app.add_handler(CallbackQueryHandler(like_callback, pattern="^like_"))

    # Guruh uchun Anti-link va Status o'chirish
    app.add_handler(MessageHandler(filters.StatusUpdate.ALL, delete_status))
    app.add_handler(MessageHandler(filters.ChatType.GROUPS & ~filters.COMMAND, anti_link))

    app.run_polling()

if __name__ == "__main__":
    main()