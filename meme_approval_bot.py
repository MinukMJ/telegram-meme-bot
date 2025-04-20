from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
import logging

# --- Config ---
TOKEN = 'os.getenv("TOKEN")'  # 🔒 Replace this safely
CHANNEL_USERNAME = '@slmemess'
ADMIN_IDS = [6715620197, 5183908956, 5753055464, 6451758507]
ADMIN_GROUP_ID = -1002168714304  # Admins-only group

# --- Setup ---
logging.basicConfig(level=logging.INFO)
pending_memes = {}  # message_id: data


def start(update: Update, context: CallbackContext):
    update.message.reply_text("👋 Welcome! Send me a meme (photo/video) to submit for approval.")


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
        "username": user.username or user.full_name,
    }

    # Placeholder buttons
    placeholder_keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("⏳ Pending...", callback_data="pending")
    ]])

    # Send to admin group
    if media_type == "photo":
        sent = context.bot.send_photo(
            chat_id=ADMIN_GROUP_ID,
            photo=file_id,
            caption=f"🆕 Meme from @{submission_data['username']} (ID: {user.id})\n\n📎 Caption: {caption}",
            reply_markup=placeholder_keyboard
        )
    else:
        sent = context.bot.send_video(
            chat_id=ADMIN_GROUP_ID,
            video=file_id,
            caption=f"🆕 Meme from @{submission_data['username']} (ID: {user.id})\n\n📎 Caption: {caption}",
            reply_markup=placeholder_keyboard
        )

    if sent:
        msg_id_str = str(sent.message_id)
        pending_memes[msg_id_str] = submission_data

        # Now set the actual buttons with valid callback_data
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Approve", callback_data=f"approve|{msg_id_str}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject|{msg_id_str}")
        ]])
        sent.edit_reply_markup(reply_markup=keyboard)

        message.reply_text("✅ Your meme has been submitted for review.")


def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data.split("|")
    action = data[0]

    # Only admins can approve/reject
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
    username = meme_data["username"]

    if action == "approve":
        credit = f"📩 Sent by @{username} — thanks for the meme!"
        if media_type == "photo":
            context.bot.send_photo(chat_id=CHANNEL_USERNAME, photo=file_id, caption=credit)
        else:
            context.bot.send_video(chat_id=CHANNEL_USERNAME, video=file_id, caption=credit)

        query.edit_message_caption("✅ Approved and posted.")
        query.answer("✅ Approved.")

    elif action == "reject":
        query.edit_message_caption("❌ Rejected by admin.")
        query.answer("⛔ Rejected.")


def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.photo | Filters.video, handle_submission))
    dp.add_handler(CallbackQueryHandler(handle_callback))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
