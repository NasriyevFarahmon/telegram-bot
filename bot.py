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

# O'zgaruvchilarni shu yerga aniq yozing
TOKEN = os.getenv("BOT_TOKEN")  # BotFather bergan token
ADMIN_ID = 5428723441           # Sizning ID
CHANNEL_ID = -1003117381416      # Kanal ID

likes_data = {}
LINK_RE = re.compile(r"(https?://|www\.|t\.me/|telegram\.me/|instagr\.am/|instagram\.com/|tiktok\.com/)", re.IGNORECASE)

# --- START BUYRUG'I ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        await update.message.reply_text("Xush kelibsiz, Admin! Kanalga yubormoqchi bo'lgan xabaringizni menga yuboring.")
    else:
        await update.message.reply_text("Салом! Ман боти расмии @DehaiSarchashma мебошам.")

# --- ADMIN PANEL: POST YARATISH ---
async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    keyboard = [[InlineKeyboardButton("✅ Kanalga yuborish", callback_data="send_to_channel")]]
    await update.message.reply_text(
        "📝 Ushbu xabarni kanalga layk tugmasi bilan yuboraymi?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        quote=True
    )
    context.user_data['pending_post'] = update.message

async def send_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    pending_msg = context.user_data.get('pending_post')

    if not pending_msg:
        await query.answer("Xato: Xabar topilmadi.", show_alert=True)
        return

    keyboard = [[InlineKeyboardButton("❤️ 0", callback_data="like_0")]]
    
    try:
        sent_msg = await context.bot.copy_message(
            chat_id=CHANNEL_ID,
            from_chat_id=pending_msg.chat_id,
            message_id=pending_msg.message_id,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        likes_data[sent_msg.message_id] = []
        await query.edit_message_text("✅ Xabar kanalga muvaffaqiyatli yuborildi!")
    except Exception as e:
        await query.edit_message_text(f"❌ Xatolik: {e}")

# --- LAYK BOSISH ---
async def like_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    msg_id = query.message.message_id
    
    if not query.data.startswith("like_"): return

    if msg_id not in likes_data: likes_data[msg_id] = []

    if user_id in likes_data[msg_id]:
        await query.answer("Siz oldin layk bosgansiz! 😊", show_alert=True)
        return

    likes_data[msg_id].append(user_id)
    count = len(likes_data[msg_id])
    
    keyboard = [[InlineKeyboardButton(f"❤️ {count}", callback_data=f"like_{count}")]]
    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
    await query.answer("Qo'llaganingiz uchun rahmat!")
    
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"📊 Yangi layk! Jami: {count}")

# --- ANTI-LINK ---
async def anti_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or update.effective_chat.type == "private": return
    
    text = (msg.text or "") + (msg.caption or "")
    if LINK_RE.search(text):
        try:
            await msg.delete()
        except: pass

async def delete_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.message.delete()
    except: pass

# --- ASOSIY ---
def main():
    if not TOKEN:
        print("XATO: BOT_TOKEN topilmadi!")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    # Handlerlarni tartibi muhim
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(send_to_channel, pattern="^send_to_channel$"))
    app.add_handler(CallbackQueryHandler(like_callback, pattern="^like_"))
    
    # Admin xabarlari (Shaxsiyda)
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, handle_admin_message))
    
    # Guruh uchun
    app.add_handler(MessageHandler(filters.StatusUpdate.ALL, delete_status))
    app.add_handler(MessageHandler(filters.ChatType.GROUPS & ~filters.COMMAND, anti_link))

    print("Bot ishga tushdi...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()