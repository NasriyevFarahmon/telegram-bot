import os
import re
import asyncio
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

# Logging sozlamalari
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# --- KONFIGURATSIYA (Koyeb'dan o'qiydi) ---
TOKEN_1 = os.getenv("BOT_TOKEN")          # Birinchi botingiz tokeni
TOKEN_2 = os.getenv("VOTE_BOT_TOKEN")     # Yangi 43-maktab boti tokeni

# 1-BOT UCHUN ADMINLAR VA KANALLAR
ADMINS_1 = [5428723441, 1375783491] 
CHANNELS_1 = {
    "📢 Dehai Sarchashma": -1001475810273,
    "📢 Kanal 2": -1003117381416
}
LINK_RE = re.compile(r"(https?://|www\.|t\.me/|telegram\.me/|instagr\.am/|instagram\.com/|tiktok\.com/)", re.IGNORECASE)
likes_data_1 = {}

# 2-BOT UCHUN ADMINLAR VA KANALLAR (43-MAKTAB)
ADMINS_2 = [1050463284, 291618110]
LOG_CHANNEL_2 = -1001849772346
likes_db_2 = {}

# ===================== 1-BOT FUNKSIYALARI =====================

async def start_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id in ADMINS_1:
        text = "👋 **Салом, Админ!**\n\n🚀 Постро фиристед..."
    else:
        text = f"👋 **Салом, {user.first_name}!**\n\n🤖 **Ман боти расмии @DehaiSarchashma мебошам.**"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def handle_admin_message_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS_1: return
    context.user_data['pending_post_id'] = update.message.message_id
    keyboard = [[InlineKeyboardButton(name, callback_data=f"send_to_{cid}")] for name, cid in CHANNELS_1.items()]
    await update.message.reply_text("📝 **Ин постро ба кадом канал мефиристед?**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

async def send_to_channel_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    target_channel_id = int(query.data.replace("send_to_", ""))
    post_id = context.user_data.get('pending_post_id')
    if not post_id: return
    keyboard = [[InlineKeyboardButton("❤️ 0", callback_data=f"like_0_{target_channel_id}")]]
    sent_msg = await context.bot.copy_message(chat_id=target_channel_id, from_chat_id=query.message.chat_id, message_id=post_id, reply_markup=InlineKeyboardMarkup(keyboard))
    likes_data_1[sent_msg.message_id] = []
    await query.edit_message_text("✅ **Ба канал фиристода шуд!**")

async def like_callback_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    msg = query.message
    data_parts = query.data.split("_")
    target_channel_id = int(data_parts[2]) if len(data_parts) > 2 else msg.chat_id
    
    if msg.message_id not in likes_data_1: likes_data_1[msg.message_id] = []
    if user.id in likes_data_1[msg.message_id]:
        await query.answer("Сиз аллакай лайк мондаед! 😊", show_alert=True)
        return
    
    likes_data_1[msg.message_id].append(user.id)
    count = len(likes_data_1[msg.message_id])
    keyboard = [[InlineKeyboardButton(f"❤️ {count}", callback_data=f"like_{count}_{target_channel_id}")]]
    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
    await query.answer('Ташаккур барои овоз! 🤩')

async def anti_link_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or update.effective_chat.type == "private": return
    text = (msg.text or "") + (msg.caption or "")
    if LINK_RE.search(text):
        member = await context.bot.get_chat_member(msg.chat_id, msg.from_user.id)
        if member.status in ["administrator", "creator"]: return
        await msg.delete()

# ===================== 2-BOT FUNKSIYALARI (43-MAKTAB) =====================

async def start_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in ADMINS_2:
        await update.message.reply_text("🏫 **43-Maktab boti tayyor!** Post yuboring.")

async def create_post_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS_2: return
    keyboard = [[InlineKeyboardButton("❤️ Ovoz berish", callback_data="vote_active")]]
    await update.message.reply_text("✅ Post tayyor! Forward qiling.", reply_markup=InlineKeyboardMarkup(keyboard))

async def vote_callback_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    msg_id = query.message.message_id
    if msg_id not in likes_db_2: likes_db_2[msg_id] = set()
    if user.id in likes_db_2[msg_id]:
        await query.answer("Siz ovoz bergansiz! 😊", show_alert=True)
        return
    likes_db_2[msg_id].add(user.id)
    count = len(likes_db_2[msg_id])
    keyboard = [[InlineKeyboardButton(f"❤️ {count}", callback_data="vote_active")]]
    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
    await query.answer("Rahmat!")
    report = f"📩 **Yangi ovoz!**\n👤 **Kim:** {user.full_name}\n📊 **Jami:** `{count}`"
    await context.bot.send_message(chat_id=LOG_CHANNEL_2, text=report, parse_mode=ParseMode.MARKDOWN)

# ===================== ASOSIY ISHGA TUSHIRISH =====================

async def main():
    # 1-Bot sozlash
    app1 = ApplicationBuilder().token(TOKEN_1).build()
    app1.add_handler(CommandHandler("start", start_1))
    app1.add_handler(CallbackQueryHandler(send_to_channel_1, pattern="^send_to_"))
    app1.add_handler(CallbackQueryHandler(like_callback_1, pattern="^like_"))
    app1.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, handle_admin_message_1))
    app1.add_handler(MessageHandler(filters.ChatType.GROUPS & ~filters.COMMAND, anti_link_1))

    # 2-Bot sozlash (43-Maktab)
    app2 = ApplicationBuilder().token(TOKEN_2).build()
    app2.add_handler(CommandHandler("start", start_2))
    app2.add_handler(CallbackQueryHandler(vote_callback_2, pattern="vote_active"))
    app2.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, create_post_2))

    # Ikkala botni bir vaqtda ishga tushirish
    await asyncio.gather(
        app1.initialize(), app1.start(), app1.updater.start_polling(drop_pending_updates=True),
        app2.initialize(), app2.start(), app2.updater.start_polling(drop_pending_updates=True)
    )
    
    while True: await asyncio.sleep(1000)

if __name__ == "__main__":
    asyncio.run(main())
