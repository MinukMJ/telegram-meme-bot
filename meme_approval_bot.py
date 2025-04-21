import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters,
    CallbackContext, CallbackQueryHandler
)
from flask import Flask, request
import telegram

# --- Config ---
TOKEN = os.getenv("Token")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g., https://your-app-name.onrender.com
CHANNEL_USERNAME = '@slmemess'
ADMIN_IDS = [6715620197, 5183908956, 5753055464, 6451758507]
ADMIN_GROUP_ID = -1002168714304

# --- Setup ---
bot = telegram.Bot(token=TOKEN)
pending_memes = {}
logging.basicConfig(level=logging.INFO)

# --- Flask App ---
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is up and running!"

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'ok'

# --- Handlers ---
def start(update: Update, context: CallbackContext):
    update.message.reply_text("👋 Welcome to Memegram Post bot! Send me a meme (photo/video) to post in the channel.")

def handle_submission(update: Update, context: CallbackContext):
    user = update.effective_user
    message = update.message

    if not message.photo and not message.video:
        message.reply_text("❌ Please send a photo or video.")
        return

    caption = message.caption or ""
    file_id = message.photo[-1].file_id if message.photo else message.video.file_id
    media_type = "photo" if message.photo else "video"

    submission_data = {
        "file_id": file_id,
        "caption": caption,
        "media_type": media_type,
        "user_id": user.id,
    }

    placeholder_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⏳ Pending...", callback_data="pending")]])

    admin_caption = f"🆕 Meme from ID: {user.id}\n\n📎 Caption: {caption}"

    if media_type == "photo":
        sent = context.bot.send_photo(chat_id=ADMIN_GROUP_ID, photo=file_id, caption=admin_caption, reply_markup=placeholder_keyboard)
    else:
        sent = context.bot.send_video(chat_id=ADMIN_GROUP_ID, video=file_id, caption=admin_caption, reply_markup=placeholder_keyboard)

    if sent:
        msg_id_str = str(sent.message_id)
        pending_memes[msg_id_str] = submission_data

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"approve|{msg_id_str}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject|{msg_id_str}")
            ]
        ])
        sent.edit_reply_markup(reply_markup=keyboard)
        message.reply_text("✅ Your meme has been submitted for review.")

def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data.split("|")
    action = data[0]

    if query.from_user.id not in ADMIN_IDS:
        query.answer("❌ You are not authorized.")
        return

    if len(data) < 2:
        query.answer("❌ Invalid callback data.")
        return

    msg_id = data[1]
    meme_data = pending_memes.get(msg_id)

    if not meme_data:
        query.answer("❌ Submission not found.")
        return

    file_id = meme_data["file_id"]
    media_type = meme_data["media_type"]
    admin_name = query.from_user.first_name or "Admin"
    credit = f"✅ Approved by {admin_name}"

    if action == "approve":
        if media_type == "photo":
            context.bot.send_photo(chat_id=CHANNEL_USERNAME, photo=file_id, caption=credit)
        else:
            context.bot.send_video(chat_id=CHANNEL_USERNAME, video=file_id, caption=credit)

        query.edit_message_caption("✅ Approved and posted.")
        query.answer("✅ Approved.")

    elif action == "reject":
        query.edit_message_caption("❌ Rejected by admin.")
        query.answer("⛔ Rejected.")

# --- Main ---
def main():
    global dispatcher
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dispatcher = dp  # Needed to call from Flask

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.photo | Filters.video, handle_submission))
    dp.add_handler(CallbackQueryHandler(handle_callback))

    # Set webhook for Telegram
    bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")

if __name__ == '__main__':
    main()
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
