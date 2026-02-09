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

# --- MA'LUMOTLAR ---
TOKEN = os.getenv("BOT_TOKEN")
ADMINS = [5428723441] 
CHANNELS = {
    "1-Kanal": -1003117381416,
    "Dehai Sarchashma": -1001475810273
}

likes_data = {}
LINK_RE = re.compile(r"(https?://|www\.|t\.me/|telegram\.me/|instagr\.am/|instagram\.com/|tiktok\.com/)", re.IGNORECASE)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id in ADMINS:
        await update.message.reply_text(
            "👋 **Салом, Админ!**\n\n🚀 Ба ман пост фиристед ва ман онро ба канал бо тугмачаи ❤️ мегузорам.",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            f"👋 **Салом, {user.first_name}!**\n\n🤖 Ман боти расмии @DehaiSarchashma мебошам.\n\n"
            "📢 Ман дар гурӯҳҳо ва каналҳо тартиботро нигоҳ медорам:\n"
            "🚫 Истинодҳои (ссылка) бегонаро нест мекунам.\n"
            "❤️ Ба постҳо тугмачаи лайк илова мекунам.",
            parse_mode=ParseMode.MARKDOWN
        )

async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return

    context.user_data['pending_post_id'] = update.message.message_id
    keyboard = [[InlineKeyboardButton(f"📢 {name}", callback_data=f"send_to_{cid}")] for name, cid in CHANNELS.items()]
    
    await update.message.reply_text(
        "📝 **Ин постро ба кадом канал мефиристед?**",
        reply_markup=InlineKeyboardMarkup(keyboard),
        reply_to_message_id=update.message.message_id,
        parse_mode=ParseMode.MARKDOWN
    )

async def send_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    target_channel_id = int(query.data.replace("send_to_", ""))
    post_id = context.user_data.get('pending_post_id')

    if not post_id:
        await query.answer("Хато: Паём ёфт нашуд!", show_alert=True)
        return

    keyboard = [[InlineKeyboardButton("❤️ 0", callback_data="like_0")]]
    
    try:
        sent_msg = await context.bot.copy_message(
            chat_id=target_channel_id,
            from_chat_id=query.message.chat_id,
            message_id=post_id,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        likes_data[sent_msg.message_id] = []
        await query.edit_message_text("✅ **Бо муваффақият ба канал фиристода шуд!**", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await query.edit_message_text(f"❌ Хатогӣ: {e}")

async def like_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    msg_id = query.message.message_id
    
    if not query.data.startswith("like_") or msg_id not in likes_data:
        if msg_id not in likes_data: likes_data[msg_id] = []
    
    if user.id in likes_data[msg_id]:
        await query.answer("Шумо аллакай лайк мондаед! 😊", show_alert=True)
        return

    likes_data[msg_id].append(user.id)
    count = len(likes_data[msg_id])
    keyboard = [[InlineKeyboardButton(f"❤️ {count}", callback_data=f"like_{count}")]]
    
    try:
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
        await query.answer("Ташаukkur!🤩")
        
        user_link = f"[{user.first_name}](tg://user?id={user.id})"
        for admin_id in ADMINS:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"❤️ **Лайки нав!**\n\n👤 Корбар: {user_link}\n📝 Post ID: `{msg_id}`",
                parse_mode=ParseMode.MARKDOWN
            )
    except: pass

async def anti_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or update.effective_chat.type == "private": return
    
    text = (msg.text or "") + (msg.caption or "")
    if LINK_RE.search(text):
        try:
            member = await context.bot.get_chat_member(msg.chat_id, msg.from_user.id)
            if member.status in ["administrator", "creator"]: return
            
            # Linkni o'chirish
            await msg.delete()
            
            # Ogohlantirish xabarini yuborish
            warning_text = (
                f"⚠️ **Ҳурматӣ {msg.from_user.mention_markdown()}!**\n\n"
                f"🚫 Дар ин гурӯҳ фиристодани истинодҳо (ссылка) манъ аст!\n"
                f"🤖 Ман боти расмии @DehaiSarchashma мебошам."
            )
            warn_msg = await context.bot.send_message(
                chat_id=msg.chat_id,
                text=warning_text,
                parse_mode=ParseMode.MARKDOWN
            )
            
            # 15 soniya kutish va ogohlantirishni o'chirish
            await asyncio.sleep(15)
            await context.bot.delete_message(chat_id=msg.chat_id, message_id=warn_msg.message_id)
            
        except Exception as e:
            logging.error(f"Anti-link error: {e}")

def main():
    if not TOKEN: return
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(send_to_channel, pattern="^send_to_-?\d+$"))
    app.add_handler(CallbackQueryHandler(like_callback, pattern="^like_"))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, handle_admin_message))
    app.add_handler(MessageHandler(filters.ChatType.GROUPS & ~filters.COMMAND, anti_link))

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()