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
likes_data_1 = {} # {message_id: [user_ids]}

# 2-BOT (43-Maktab)
ADMINS_2 = [1050463284, 291618110]
CHANNELS_2 = {"🏫 43-Maktab kanali": -1003182749320}
likes_db_2 = {} # {message_id: [user_ids]}

# ===================== 1-BOT (DEHAI SARCHASHMA - TOJIKCHA) =====================

async def start_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id in ADMINS_1:
        text = "👋 **Салом, Муҳтарам Админ!**\n\nБа бот хуш омадед. Шумо метавонед матн, акс ё видеои худро барои нашр дар канал ирсол намоед."
    else:
        text = f"👋 **Салом, {user.first_name}!**\n\n🤖 **Ман боти расмии ҷамоати @DehaiSarchashma мебошам.** Барои маълумоти бештар ба канали мо обуна шавед."
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def handle_admin_message_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS_1: return
    context.user_data['p_post_1'] = update.message.message_id
    # Post sarlavhasini saqlab qo'yamiz
    context.user_data['p_title_1'] = (update.message.text or update.message.caption or "Акс/Видео")[:30] + "..."
    
    keyboard = [[InlineKeyboardButton(name, callback_data=f"send1_{cid}")] for name, cid in CHANNELS_1.items()]
    await update.message.reply_text("📝 **Лутфан, барои нашри ин мавод канали лозимиро интихоб намоед:**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

async def send_to_channel_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    target_cid = int(query.data.split("_")[1])
    post_id = context.user_data.get('p_post_1')
    post_title = context.user_data.get('p_title_1')
    if not post_id: return
    
    kb = [[InlineKeyboardButton("❤️ 0", callback_data=f"l1_{target_cid}")]]
    sent = await context.bot.copy_message(chat_id=target_cid, from_chat_id=query.from_user.id, message_id=post_id, reply_markup=InlineKeyboardMarkup(kb))
    
    likes_data_1[sent.message_id] = {"users": [], "title": post_title, "chat_id": target_cid}
    await query.edit_message_text("✅ **Мавод бо муваффақият ба канал фиристода шуд!**")

async def like_callback_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    msg = query.message
    mid = msg.message_id
    
    if mid not in likes_data_1: return
    if user.id in likes_data_1[mid]["users"]:
        await query.answer("Шумо аллакай ба ин мавод баҳо додаед! 😊", show_alert=True)
        return
    
    likes_data_1[mid]["users"].append(user.id)
    count = len(likes_data_1[mid]["users"])
    target_cid = likes_data_1[mid]["chat_id"]
    
    kb = [[InlineKeyboardButton(f"❤️ {count}", callback_data=f"l1_{target_cid}")]]
    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(kb))
    await query.answer('Ташаккур барои баҳоятон! 🤩')

    # ADMINGA TO'LIQ HISOBOT
    post_link = f"https://t.me/c/{str(target_cid).replace('-100', '')}/{mid}"
    user_link = f"[{user.full_name}](tg://user?id={user.id})"
    
    report = (
        f"📊 **Ҳисоботи нав (Dehai Sarchashma):**\n\n"
        f"👤 **Корбар:** {user_link}\n"
        f"🆔 **ID:** `{user.id}`\n"
        f"📝 **Мавод:** {likes_data_1[mid]['title']}\n"
        f"🔗 **Пайванд:** [Ин ҷоро пахш кунед]({post_link})\n\n"
        f"❤️ **Миқдори умумии лайкҳо:** `{count}`"
    )
    for admin_id in ADMINS_1:
        try: await context.bot.send_message(chat_id=admin_id, text=report, parse_mode=ParseMode.MARKDOWN)
        except: pass

# ===================== 2-BOT (43-MAKTAB - O'ZBEKCHA) =====================

async def start_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id in ADMINS_2:
        await update.message.reply_text("🏫 **43-maktab Rasmiy Botiga xush kelibsiz!**\n\nAdmin paneldasiz. Kanalga joylash uchun biror ma'lumot (matn, rasm yoki video) yuboring.")
    else:
        kb = [[InlineKeyboardButton("✍️ Murojaat yo'llash", callback_data="murojaat_yuborish")]]
        await update.message.reply_text(
            f"Assalomu alaykum, {user.first_name}!\n\nUshbu bot orqali 43-maktab ma'muriyatiga o'z taklif va murojaatlaringizni yuborishingiz mumkin.",
            reply_markup=InlineKeyboardMarkup(kb)
        )

async def handle_2_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id in ADMINS_2:
        # Murojaatga javob berish
        if update.message.reply_to_message and "🆔 ID:" in update.message.reply_to_message.text:
            try:
                u_id = int(update.message.reply_to_message.text.split("🆔 ID:")[1].split("\n")[0].strip().replace("`", ""))
                await context.bot.send_message(chat_id=u_id, text=f"🔔 **Maktab ma'muriyati javobi:**\n\n{update.message.text}")
                await update.message.reply_text("✅ Javobingiz foydalanuvchiga yetkazildi.")
                return
            except: pass

        context.user_data['p_post_2'] = update.message.message_id
        context.user_data['p_title_2'] = (update.message.text or update.message.caption or "Media fayl")[:30] + "..."
        kb = [[InlineKeyboardButton(n, callback_data=f"s2_{cid}")] for n, cid in CHANNELS_2.items()]
        await update.message.reply_text("📝 **Ushbu postni qaysi kanalga nashr etamiz?**", reply_markup=InlineKeyboardMarkup(kb))
    
    else:
        if context.user_data.get('waiting_murojaat'):
            report = f"📩 **Yangi rasmiy murojaat!**\n\n👤 **Yuboruvchi:** {user.full_name}\n🆔 ID: `{user.id}`\n\n📝 **Murojaat matni:**\n{update.message.text}"
            for admin_id in ADMINS_2:
                try: await context.bot.send_message(chat_id=admin_id, text=report, parse_mode=ParseMode.MARKDOWN)
                except: pass
            context.user_data['waiting_murojaat'] = False
            await update.message.reply_text("✅ Murojaatingiz qabul qilindi. Tez orada ko'rib chiqiladi.")

async def send_to_channel_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    target_cid = int(query.data.split("_")[1])
    post_id = context.user_data.get('p_post_2')
    post_title = context.user_data.get('p_title_2')
    if not post_id: return
    kb = [[InlineKeyboardButton("❤️ Ovoz berish", callback_data=f"l2_{target_cid}")]]
    sent = await context.bot.copy_message(chat_id=target_cid, from_chat_id=query.from_user.id, message_id=post_id, reply_markup=InlineKeyboardMarkup(kb))
    likes_db_2[sent.message_id] = {"users": [], "title": post_title, "chat_id": target_cid}
    await query.edit_message_text("✅ Post muvaffaqiyatli kanalga joylandi!")

async def like_callback_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    mid, target_cid = query.message.message_id, int(query.data.split("_")[1])
    
    try:
        m = await context.bot.get_chat_member(chat_id=target_cid, user_id=user.id)
        if m.status in ["left", "kicked"]:
            await query.answer("🚫 Ovoz berish uchun kanalga a'zo bo'lishingiz shart!", show_alert=True); return
    except: pass

    if mid not in likes_db_2: return
    if user.id in likes_db_2[mid]["users"]:
        await query.answer("Siz ushbu xabarga ovoz berib bo'lgansiz! 😊", show_alert=True); return
    
    likes_db_2[mid]["users"].append(user.id)
    count = len(likes_db_2[mid]["users"])
    kb = [[InlineKeyboardButton(f"❤️ {count}", callback_data=f"l2_{target_cid}")]]
    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(kb))
    await query.answer("Ovozingiz qabul qilindi!")

    # ADMINGA TO'LIQ HISOBOT
    post_link = f"https://t.me/c/{str(target_cid).replace('-100', '')}/{mid}"
    user_link = f"[{user.full_name}](tg://user?id={user.id})"
    
    report = (
        f"❤️ **Yangi ovoz berildi (43-Maktab):**\n\n"
        f"👤 **Foydalanuvchi:** {user_link}\n"
        f"🆔 **ID:** `{user.id}`\n"
        f"📝 **Post sarlavhasi:** {likes_db_2[mid]['title']}\n"
        f"🔗 **Postga havola:** [Ko'rish uchun bosing]({post_link})\n\n"
        f"📊 **Jami to'plangan ovozlar:** `{count}`"
    )
    for aid in ADMINS_2:
        try: await context.bot.send_message(chat_id=aid, text=report, parse_mode=ParseMode.MARKDOWN)
        except: pass

async def murojaat_btn_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['waiting_murojaat'] = True
    await query.edit_message_text("📝 Marhamat, murojaatingizni batafsil yozib yuboring:")

# ===================== ISHGA TUSHIRISH (RUN) =====================

async def main():
    app1 = ApplicationBuilder().token(TOKEN_1).build()
    app1.add_handler(CommandHandler("start", start_1))
    app1.add_handler(CallbackQueryHandler(send_to_channel_1, pattern="^send1_"))
    app1.add_handler(CallbackQueryHandler(like_callback_1, pattern="^l1_"))
    app1.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, handle_admin_message_1))

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
