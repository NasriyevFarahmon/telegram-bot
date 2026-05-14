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

TOKEN = os.getenv("BOT_TOKEN")

ADMINS = [5428723441, 1375783491] 



CHANNELS = {

    "📢 Dehai Sarchashma": -1001475810273,

    "📢 Kanal 2": -1003117381416

}



LINK_RE = re.compile(r"(https?://|www\.|t\.me/|telegram\.me/|instagr\.am/|instagram\.com/|tiktok\.com/)", re.IGNORECASE)

likes_data = {}



# --- FUNKSIYALAR ---



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    if user.id in ADMINS:

        text = "👋 **Салом, Админ!**\n\n🚀 Постро фиристед, то ман онро бо тугмачаи ❤️ ба каналҳо гузорам. Рухсат танҳо бо суперадмин ва ИД: 1375783491 Мирожидин Қурбонов ҳаст"

    else:

        text = (

            f"👋 **Салом, {user.first_name}!**\n\n"

            "🤖 **Ман боти расмии @DehaiSarchashma мебошам.**\n\n"

            "🛠 **Вазифаҳои ман:**\n"

            "✅ Тоза кардани эълонҳои таблиғотӣ (link) дар гурӯҳ\n"

            "✅ Нест кардани паёмҳои «омад/рафт»-и корбарон дар гурӯҳ\n"

            "✅ Гузоштани постҳои ҷолиб дар канал бо тугмачаи лайк ❤️\n\n"

            "🤝 Барои саволҳо ва ҳамкорӣ метавонед ба @Nasriyev_F муроҷиат кунед."

        )

    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)



async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id not in ADMINS: return

    context.user_data['pending_post_id'] = update.message.message_id

    keyboard = [[InlineKeyboardButton(name, callback_data=f"send_to_{cid}")] for name, cid in CHANNELS.items()]

    await update.message.reply_text("📝 **Ин постро ба кадом канал мефиристед?**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)



async def send_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    target_channel_id = int(query.data.replace("send_to_", ""))

    post_id = context.user_data.get('pending_post_id')



    if not post_id:

        await query.answer("❌ Хато!", show_alert=True)

        return



    keyboard = [[InlineKeyboardButton("❤️ 0", callback_data=f"like_0_{target_channel_id}")]]

    try:

        sent_msg = await context.bot.copy_message(chat_id=target_channel_id, from_chat_id=query.message.chat_id, message_id=post_id, reply_markup=InlineKeyboardMarkup(keyboard))

        likes_data[sent_msg.message_id] = []

        await query.edit_message_text("✅ **Ба канал фиристода шуд!**", parse_mode=ParseMode.MARKDOWN)

    except Exception as e:

        await query.edit_message_text(f"❌ Хатогӣ: {e}")



async def like_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    user = query.from_user

    msg = query.message

    data_parts = query.data.split("_")

    target_channel_id = int(data_parts[2]) if len(data_parts) > 2 else msg.chat_id



    try:

        member = await context.bot.get_chat_member(chat_id=target_channel_id, user_id=user.id)

        if member.status not in ["member", "administrator", "creator"]:

            await query.answer("🚫 Барои лайк мондан, аввал ба канал обуна шавед!", show_alert=True)

            return

    except: pass



    if msg.message_id not in likes_data: likes_data[msg.message_id] = []

    if user.id in likes_data[msg.message_id]:

        await query.answer("Ба озмуни Наврўз шумо аллакай лайк мондаед! 😊", show_alert=True)

        return



    likes_data[msg.message_id].append(user.id)

    count = len(likes_data[msg.message_id])

    keyboard = [[InlineKeyboardButton(f"❤️ {count}", callback_data=f"like_{count}_{target_channel_id}")]]

    

    try:

        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))

        await query.answer('Ташаккур барои овоз доданатон ба озмуни "Наврӯз"!🤩')

        

        # --- ADMIN UCHUN XABARNOMA QISMI ---

        post_link = f"https://t.me/c/{str(target_channel_id)[4:]}/{msg.message_id}"

        user_name = f"[{user.full_name}](tg://user?id={user.id})"

        channel_name = next((name for name, cid in CHANNELS.items() if cid == target_channel_id), "Канал")

        

        admin_text = (

            f"❤️ **Лайки нав!**\n\n"

            f"👤 **Корбар:** {user_name}\n"

            f"📢 **Канал:** {channel_name}\n"

            f"🔗 [Ба пост нигоҳ]({post_link})\n"

            f"📊 **Ҷамъи лайкҳо:** `{count}`"

        )

        

        for admin_id in ADMINS:

            try:

                await context.bot.send_message(chat_id=admin_id, text=admin_text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

            except: pass

    except Exception as e:

        logging.error(f"Like error: {e}")



async def anti_link(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg = update.message

    if not msg or update.effective_chat.type == "private": return

    text = (msg.text or "") + (msg.caption or "")

    if LINK_RE.search(text):

        try:

            member = await context.bot.get_chat_member(msg.chat_id, msg.from_user.id)

            if member.status in ["administrator", "creator"]: return

            await msg.delete()

            warn = await context.bot.send_message(

                chat_id=msg.chat_id,

                text=f"⚠️ **Илтимос {msg.from_user.mention_markdown()}!**\n🚫 Истинод манъ аст! Mан боти расмии @DehaiSarchashma ҳастам",

                parse_mode=ParseMode.MARKDOWN

            )

            await asyncio.sleep(15)

            await warn.delete()

        except: pass



async def delete_status_updates(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        await update.message.delete()

    except: pass



def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(CallbackQueryHandler(send_to_channel, pattern="^send_to_"))

    app.add_handler(CallbackQueryHandler(like_callback, pattern="^like_"))

    app.add_handler(MessageHandler(filters.StatusUpdate.ALL, delete_status_updates))

    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, handle_admin_message))

    app.add_handler(MessageHandler(filters.ChatType.GROUPS & ~filters.COMMAND, anti_link))

    app.run_polling(drop_pending_updates=True)



if __name__ == "__main__":

    main()
