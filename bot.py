import os
import re
import logging
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

# Logging (Xatolarni ko'rish uchun)
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# --- MA'LUMOTLAR ---
TOKEN = os.getenv("BOT_TOKEN")  # Tokeningizni shu yerga qo'ying
ADMIN_ID = 5428723441           # Sizning ID
CHANNEL_ID = -1003117381416      # Kanal ID

likes_data = {}
LINK_RE = re.compile(r"(https?://|www\.|t\.me/|telegram\.me/|instagr\.am/|instagram\.com/|tiktok\.com/)", re.IGNORECASE)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        await update.message.reply_text("👋 Salom Admin! Kanalga yubormoqchi bo'lgan postni (rasm, matn) menga yuboring.")
    else:
        await update.message.reply_text("Салом! Ман боти расмии @DehaiSarchashma мебошам.")

async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Admin ekanligini qat'iy tekshiramiz
    if update.effective_user.id != ADMIN_ID:
        return

    # Xabar turidan qat'i nazar (rasm, video, matn) uni saqlaymiz
    context.user_data['pending_post_id'] = update.message.message_id
    
    keyboard = [[InlineKeyboardButton("✅ Kanalga yuborish", callback_data="send_to_channel")]]
    await update.message.reply_text(
        "📝 Ushbu postni kanalga layk tugmasi bilan yuboraymi?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        reply_to_message_id=update.message.message_id
    )

async def send_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    post_id = context.user_data.get('pending_post_id')

    if not post_id:
        await query.answer("Xato: Xabar topilmadi!", show_alert=True)
        return

    # Kanalda chiqadigan layk tugmasi
    keyboard = [[InlineKeyboardButton("❤️ 0", callback_data="like_0")]]
    
    try:
        # Admin yuborgan xabarni kanalga nusxalaymiz
        sent_msg = await context.bot.copy_message(
            chat_id=CHANNEL_ID,
            from_chat_id=query.message.chat_id,
            message_id=post_id,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        likes_data[sent_msg.message_id] = []
        await query.edit_message_text("✅ Muvaffaqiyatli yuborildi!")
    except Exception as e:
        await query.edit_message_text(f"❌ Xatolik yuz berdi: {e}")

async def like_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    msg_id = query.message.message_id
    
    if not query.data.startswith("like_"):
        return

    if msg_id not in likes_data:
        likes_data[msg_id] = []

    if user_id in likes_data[msg_id]:
        await query.answer("Siz oldin layk bosgansiz! 😊", show_alert=True)
        return

    likes_data[msg_id].append(user_id)
    count = len(likes_data[msg_id])
    
    keyboard = [[InlineKeyboardButton(f"❤️ {count}", callback_data=f"like_{count}")]]
    
    try:
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
        await query.answer("Rahmat!")
        
        # Adminga xabar
        await context.bot.send_message(
            chat_id=ADMIN_ID, 
            text=f"📊 Yangi layk!\nPost ID: {msg_id}\nJami: {count} ta"
        )
    except:
        pass

async def anti_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or update.effective_chat.type == "private": return
    
    # Linkni tekshirish
    text = (msg.text or "") + (msg.caption or "")
    if LINK_RE.search(text):
        try:
            # Agar xabarni yuborgan odam admin bo'lsa o'chirmaymiz
            member = await context.bot.get_chat_member(msg.chat_id, msg.from_user.id)
            if member.status in ["administrator", "creator"]: return
            await msg.delete()
        except: pass

def main():
    if not TOKEN: return

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(send_to_channel, pattern="^send_to_channel$"))
    app.add_handler(CallbackQueryHandler(like_callback, pattern="^like_"))
    
    # Faqat shaxsiy chatda admin yuborgan xabarlarni tutish
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, handle_admin_message))
    
    # Guruhlarda linklarni o'chirish
    app.add_handler(MessageHandler(filters.ChatType.GROUPS, anti_link))

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()