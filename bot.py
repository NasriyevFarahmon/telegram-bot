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

# --- KONFIGURATSIYA ---
TOKEN_1 = os.getenv("BOT_TOKEN")
TOKEN_2 = os.getenv("VOTE_BOT_TOKEN")

# 1-BOT (Dehai Sarchashma)
ADMINS_1 = [5428723441, 1375783491] 
CHANNELS_1 = {"📢 Dehai Sarchashma": -1001475810273, "📢 Kanal 2": -1003117381416}
LINK_RE = re.compile(r"(https?://|www\.|t\.me/|telegram\.me/|instagr\.am/|instagram\.com/|tiktok\.com/)", re.IGNORECASE)
likes_data_1 = {}

# 2-BOT (43-Maktab)
ADMINS_2 = [1050463284, 291618110]
CHANNELS_2 = {"🏫 43-Maktab kanali": -1003182749320}
likes_db_2 = {}

# ===================== 1-BOT FUNKSIYALARI (O'ZGARMADI) =====================

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
    target_cid = int(query.data.replace("send_to_", ""))
    post_id = context.user_data.get('pending_post_id')
    if not post_id: return
    keyboard = [[InlineKeyboardButton("❤️ 0", callback_data=f"like_0_{target_cid}")]]
    sent_msg = await context.bot.copy_message(chat_id=target_cid, from_chat_id=query.message.chat_id, message_id=post_id, reply_markup=InlineKeyboardMarkup(keyboard))
    likes_data_1[sent_msg.message_id] = []
    await query.edit_message_text("✅ **Ба канал фиристода шуд!**")

async def like_callback_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    msg = query.message
    if msg.message_id not in likes_data_1: likes_data_1[msg.message_id] = []
    if user.id in likes_data_1[msg.message_id]:
        await query.answer("Аллакай лайк мондаед! 😊", show_alert=True)
        return
    
    likes_data_1[msg.message_id].append(user.id)
    count = len(likes_data_1[msg.message_id])
    target_cid = int(query.data.split("_")[2])
    keyboard = [[InlineKeyboardButton(f"❤️ {count}", callback_data=f"like_{count}_{target_cid}")]]
    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
    await query.answer('Ташаккур! 🤩')

    report = f"📊 **Dehai Sarchashma: Yangi layk!**\n👤 **Kim:** {user.full_name}\n🆔 **ID:** `{user.id}`\n❤️ **Jami:** {count}"
    for admin_id in ADMINS_1:
        try: await context.bot.send_message(chat_id=admin_id, text=report, parse_mode=ParseMode.MARKDOWN)
        except: pass

async def anti_link_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or update.effective_chat.type == "private": return
    text = (msg.text or "") + (msg.caption or "")
    if LINK_RE.search(text):
        try:
            member = await context.bot.get_chat_member(msg.chat_id, msg.from_user.id)
            if member.status in ["administrator", "creator"]: return
            await msg.delete()
        except: pass

# ===================== 2-BOT FUNKSIYALARI (YANGILANDI) =====================

async def start_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id in ADMINS_2:
        await update.message.reply_text("🏫 **43-Maktab boti (Admin panel)**\n\nKanalga post yuborish uchun rasm yoki matn yuboring.")
    else:
        kb = [[InlineKeyboardButton("✍️ Murojaat yuborish", callback_data="murojaat_yuborish")]]
        await update.message.reply_text(
            f"Salom {user.first_name}! 43-maktab botiga xush kelibsiz.\n\n"
            "Maktab ma'muriyatiga taklif yoki murojaatlaringiz bo'lsa, quyidagi tugmani bosing:",
            reply_markup=InlineKeyboardMarkup(kb)
        )

async def handle_2_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # ADMIN LOGIKASI: Post yuborish
    if user.id in ADMINS_2:
        # Agar admin kimdirning murojaatiga javob yozayotgan bo'lsa
        if update.message.reply_to_message and "🆔 ID:" in update.message.reply_to_message.text:
            try:
                user_id = int(update.message.reply_to_message.text.split("🆔 ID:")[1].split("\n")[0].strip().replace("`", ""))
                await context.bot.send_message(chat_id=user_id, text=f"🔔 **Maktab ma'muriyatidan javob:**\n\n{update.message.text}")
                await update.message.reply_text("✅ Javobingiz foydalanuvchiga yuborildi.")
                return
            except: pass

        context.user_data['p_post_2'] = update.message.message_id
        keyboard = [[InlineKeyboardButton(n, callback_data=f"s2_{cid}")] for n, cid in CHANNELS_2.items()]
        await update.message.reply_text("❓ Ushbu postni qaysi kanalga yuboramiz?", reply_markup=InlineKeyboardMarkup(keyboard))
    
    # FOYDALANUVCHI LOGIKASI: Murojaat qabul qilish
    else:
        if context.user_data.get('waiting_murojaat'):
            report = f"📩 **Yangi murojaat!**\n👤 **Kimdan:** {user.full_name}\n🆔 ID: `{user.id}`\n\n📝 **Matn:** {update.message.text}"
            for admin_id in ADMINS_2:
                try: await context.bot.send_message(chat_id=admin_id, text=report, parse_mode=ParseMode.MARKDOWN)
                except: pass
            context.user_data['waiting_murojaat'] = False
            await update.message.reply_text("✅ Murojaatingiz yuborildi. Tezpada javob olasiz.")

async def send_to_channel_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    target_cid = int(query.data.split("_")[1])
    post_id = context.user_data.get('p_post_2')
    if not post_id: return
    kb = [[InlineKeyboardButton("❤️ Ovoz berish", callback_data=f"l2_{target_cid}")]]
    await context.bot.copy_message(chat_id=target_cid, from_chat_id=query.from_user.id, message_id=post_id, reply_markup=InlineKeyboardMarkup(kb))
    await query.edit_message_text("✅ Post kanalga yuborildi!")

async def like_callback_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    mid, target_cid = query.message.message_id, int(query.data.split("_")[1])
    try:
        m = await context.bot.get_chat_member(chat_id=target_cid, user_id=user.id)
        if m.status in ["left", "kicked"]:
            await query.answer("🚫 Kanalga a'zo bo'ling!", show_alert=True); return
    except: pass
    if mid not in likes_db_2: likes_db_2[mid] = []
    if user.id in likes_db_2[mid]:
        await query.answer("Faqat bir marta! 😊", show_alert=True); return
    likes_db_2[mid].append(user.id)
    kb = [[InlineKeyboardButton(f"❤️ {len(likes_db_2[mid])}", callback_data=f"l2_{target_cid}")]]
    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(kb))
    report = f"❤️ **43-Maktab Ovoz!**\n👤: {user.full_name}\n🆔: `{user.id}`\n📊 Jami: {len(likes_db_2[mid])}"
    for aid in ADMINS_2:
        try: await context.bot.send_message(chat_id=aid, text=report, parse_mode=ParseMode.MARKDOWN)
        except: pass

async def murojaat_btn_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['waiting_murojaat'] = True
    await query.edit_message_text("📝 Murojaat matnini yozib yuboring:")

# ===================== ISHGA TUSHIRISH =====================

async def main():
    app1 = ApplicationBuilder().token(TOKEN_1).build()
    app1.add_handler(CommandHandler("start", start_1))
    app1.add_handler(CallbackQueryHandler(send_to_channel_1, pattern="^send_to_"))
    app1.add_handler(CallbackQueryHandler(like_callback_1, pattern="^like_"))
    app1.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, handle_admin_message_1))
    app1.add_handler(MessageHandler(filters.ChatType.GROUPS & ~filters.COMMAND, anti_link_1))

    app2 = ApplicationBuilder().token(TOKEN_2).build()
    app2.add_handler(CommandHandler("start", start_2))
    app2.add_handler(CallbackQueryHandler(send_to_channel_2, pattern="^s2_"))
    app2.add_handler(CallbackQueryHandler(like_callback_2, pattern="^l2_"))
    app2.add_handler(CallbackQueryHandler(murojaat_btn_handler, pattern="murojaat_yuborish"))
    app2.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, handle_2_logic))

    await app1.initialize(); await app2.initialize()
    await app1.start(); await app2.start()
    await asyncio.gather(app1.updater.start_polling(drop_pending_updates=True), app2.updater.start_polling(drop_pending_updates=True))
    while True: await asyncio.sleep(1000)

if __name__ == "__main__":
    asyncio.run(main())
