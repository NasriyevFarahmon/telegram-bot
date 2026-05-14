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

# Logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# --- KONFIGURATSIYA (Koyeb Environment Variables) ---
TOKEN_1 = os.getenv("BOT_TOKEN")
TOKEN_2 = os.getenv("VOTE_BOT_TOKEN")

# 1-BOT (Dehai Sarchashma) ma'lumotlari
ADMINS_1 = [5428723441, 1375783491] 
CHANNELS_1 = {"📢 Dehai Sarchashma": -1001475810273, "📢 Kanal 2": -1003117381416}
LINK_RE = re.compile(r"(https?://|www\.|t\.me/|telegram\.me/|instagr\.am/|instagram\.com/|tiktok\.com/)", re.IGNORECASE)
likes_data_1 = {}

# 2-BOT (43-Maktab) ma'lumotlari
ADMINS_2 = [1050463284, 291618110]
CHANNELS_2 = {"🏫 43-Maktab kanali": -1001849772346} # Ovoz yig'iladigan kanal IDsi
likes_db_2 = {} # {message_id: [user_id1, user_id2]}

# ===================== 1-BOT (O'ZGARMAGAN) =====================

async def start_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id in ADMINS_1:
        text = "👋 **Салом, Админ!**\n\n🚀 Постро фиристед..."
    else:
        text = f"👋 **Салом, {user.first_name}!**\n\n🤖 **Ман боти расмии @DehaiSarchashma мебошам.**"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def handle_admin_message_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS_1: return
    context.user_data['p_post_1'] = update.message.message_id
    keyboard = [[InlineKeyboardButton(n, callback_data=f"s1_{cid}")] for n, cid in CHANNELS_1.items()]
    await update.message.reply_text("📝 **Ин постро ба кадом kanal мефиристед?**", reply_markup=InlineKeyboardMarkup(keyboard))

async def send_to_channel_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    target_cid = int(query.data.replace("s1_", ""))
    post_id = context.user_data.get('p_post_1')
    if not post_id: return
    kb = [[InlineKeyboardButton("❤️ 0", callback_data=f"l1_0_{target_cid}")]]
    sent = await context.bot.copy_message(chat_id=target_cid, from_chat_id=query.message.chat_id, message_id=post_id, reply_markup=InlineKeyboardMarkup(kb))
    likes_data_1[sent.message_id] = []
    await query.edit_message_text("✅ **Ба канал фиристода шуд!**")

async def like_callback_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid, mid = query.from_user.id, query.message.message_id
    if mid not in likes_data_1: likes_data_1[mid] = []
    if uid in likes_data_1[mid]:
        await query.answer("Сиз аллакай лайk мондаед! 😊", show_alert=True)
        return
    likes_data_1[mid].append(uid)
    count = len(likes_data_1[mid])
    target_cid = int(query.data.split("_")[2])
    kb = [[InlineKeyboardButton(f"❤️ {count}", callback_data=f"l1_{count}_{target_cid}")]]
    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(kb))
    await query.answer('Ташаккур! 🤩')

async def anti_link_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or update.effective_chat.type == "private": return
    if LINK_RE.search((msg.text or "") + (msg.caption or "")):
        try:
            m = await context.bot.get_chat_member(msg.chat_id, msg.from_user.id)
            if m.status not in ["administrator", "creator"]: await msg.delete()
        except: pass

# ===================== 2-BOT (YANGILANGAN MANTIQ) =====================

async def start_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in ADMINS_2:
        await update.message.reply_text("🏫 **43-Maktab boti tayyor!** Post yuboring.")

async def handle_admin_message_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS_2: return
    context.user_data['p_post_2'] = update.message.message_id
    keyboard = [[InlineKeyboardButton(n, callback_data=f"s2_{cid}")] for n, cid in CHANNELS_2.items()]
    await update.message.reply_text("❓ Ushbu postni qaysi kanalga yuboramiz?", reply_markup=InlineKeyboardMarkup(keyboard))

async def send_to_channel_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    target_cid = int(query.data.replace("s2_", ""))
    post_id = context.user_data.get('p_post_2')
    if not post_id: return
    kb = [[InlineKeyboardButton("❤️ Ovoz berish", callback_data=f"l2_{target_cid}")]]
    sent = await context.bot.copy_message(chat_id=target_cid, from_chat_id=query.message.chat_id, message_id=post_id, reply_markup=InlineKeyboardMarkup(kb))
    likes_db_2[sent.message_id] = []
    await query.edit_message_text("✅ Post kanalga yuborildi va ❤️ tugmasi qo'shildi.")

async def like_callback_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    mid = query.message.message_id
    target_cid = int(query.data.split("_")[1])

    # 1. A'zolikni tekshirish
    try:
        member = await context.bot.get_chat_member(chat_id=target_cid, user_id=user.id)
        if member.status in ["left", "kicked"]:
            await query.answer("🚫 Ovoz berish uchun kanalga a'zo bo'lishingiz kerak!", show_alert=True)
            return
    except: pass

    # 2. Takroriy ovozni tekshirish
    if mid not in likes_db_2: likes_db_2[mid] = []
    if user.id in likes_db_2[mid]:
        await query.answer("Siz faqat bir marta ovoz bera olasiz! 😊", show_alert=True)
        return

    # 3. Ovozni qabul qilish
    likes_db_2[mid].append(user.id)
    count = len(likes_db_2[mid])
    kb = [[InlineKeyboardButton(f"❤️ {count}", callback_data=f"l2_{target_cid}")]]
    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(kb))
    await query.answer("Rahmat! Ovozingiz qabul qilindi.")

    # 4. Adminga hisobot yuborish
    report = f"❤️ **Yangi ovoz!**\n👤 **Kim:** {user.full_name}\n🆔 **ID:** `{user.id}`\n📊 **Jami ovoz:** `{count}`"
    for admin_id in ADMINS_2:
        try: await context.bot.send_message(chat_id=admin_id, text=report, parse_mode=ParseMode.MARKDOWN)
        except: pass

# ===================== ISHGA TUSHIRISH =====================

async def main():
    app1 = ApplicationBuilder().token(TOKEN_1).build()
    app1.add_handler(CommandHandler("start", start_1))
    app1.add_handler(CallbackQueryHandler(send_to_channel_1, pattern="^s1_"))
    app1.add_handler(CallbackQueryHandler(like_callback_1, pattern="^l1_"))
    app1.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, handle_admin_message_1))
    app1.add_handler(MessageHandler(filters.ChatType.GROUPS & ~filters.COMMAND, anti_link_1))

    app2 = ApplicationBuilder().token(TOKEN_2).build()
    app2.add_handler(CommandHandler("start", start_2))
    app2.add_handler(CallbackQueryHandler(send_to_channel_2, pattern="^s2_"))
    app2.add_handler(CallbackQueryHandler(like_callback_2, pattern="^l2_"))
    app2.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, handle_admin_message_2))

    await app1.initialize()
    await app2.initialize()
    await app1.start()
    await app2.start()
    
    await asyncio.gather(
        app1.updater.start_polling(drop_pending_updates=True),
        app2.updater.start_polling(drop_pending_updates=True)
    )
    while True: await asyncio.sleep(1000)

if __name__ == "__main__":
    asyncio.run(main())
