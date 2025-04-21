Certainly! I'll rewrite your code to use the long polling method instead of a webhook. Long polling retrieves updates directly from Telegram's servers by periodically checking for new messages, so you won't need Flask or a webhook.
Here’s your updated code with the necessary changes applied:
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, CallbackContext,
    CallbackQueryHandler, Filters
)

# --- Config ---
TOKEN = os.getenv("Token")
CHANNEL_USERNAME = '@slmemess'
ADMIN_IDS = [6715620197, 5183908956, 5753055464, 6451758507]
ADMIN_GROUP_ID = -1002168714304

# --- Setup ---
bot = Bot(token=TOKEN)
pending_memes = {}
logging.basicConfig(level=logging.INFO)

# --- Handlers ---
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "👋 Welcome to Memegram Post bot! Send me a meme (photo/video) to post in the channel."
    )

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

    placeholder_keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("⏳ Pending...", callback_data="pending")]]
    )

    admin_caption = f"🆕 Meme from ID: {user.id}\n\n📎 Caption: {caption}"

    if media_type == "photo":
        sent = context.bot.send_photo(
            chat_id=ADMIN_GROUP_ID, photo=file_id,
            caption=admin_caption, reply_markup=placeholder_keyboard
        )
    else:
        sent = context.bot.send_video(
            chat_id=ADMIN_GROUP_ID, video=file_id,
            caption=admin_caption, reply_markup=placeholder_keyboard
        )

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
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.photo | Filters.video, handle_submission))
    dispatcher.add_handler(CallbackQueryHandler(handle_callback))

    # Start the bot with polling
    logging.info("Bot is starting with long polling...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()


Key Changes:
- Removed Flask & Webhook:- Removed all Flask-related code, along with bot.set_webhook and bot.delete_webhook.

- Integrated Long Polling:- Used the Updater from telegram.ext to poll Telegram's servers for updates using updater.start_polling().

- Simplified Setup:- No external server is needed. The bot will directly handle updates using long polling.


Deployment Tips:
- Run the bot on a system that stays online (e.g., a VPS or local system with a screen session).
- Ensure that your environment variables (Token) are properly set.

Let me know if you need any further assistance or customizations! 😊
