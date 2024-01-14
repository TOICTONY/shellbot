import os
import subprocess
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from pymongo import MongoClient
from io import BytesIO
from PIL import Image
import ffmpeg

API_ID = 'YOUR_TELEGRAM_API_ID'
API_HASH = 'YOUR_TELEGRAM_API_HASH'
TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
SAVE_PATH = 'path/to/save/files'
MONGO_URI = 'YOUR_MONGO_URI'
MONGO_DB_NAME = 'file_bot_db'
OWNER_ID = 'YOUR_OWNER_ID'  # Replace with your Telegram user ID

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]
user_collection = db['users']

class ShellBot:
    def __init__(self):
        self.pending_files = {}

def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user_collection.update_one({'_id': user_id}, {'$set': {'user_id': user_id}}, upsert=True)

    welcome_message = (
        "Welcome to the Rename File Bot! 🌟\n"
        "Send me a file, and I will save it with a new name. 📂"
    )
    update.message.reply_text(welcome_message)

def handle_file(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    file_id = update.message.document.file_id
    file_info = context.bot.get_file(file_id)
    file_path = file_info.file_path
    file_extension = os.path.splitext(file_path)[1]

    new_filename = f"{file_id}{file_extension}"
    file_local_path = os.path.join(SAVE_PATH, new_filename)

    thumbnail_file_id = update.message.document.thumb.file_id if update.message.document.thumb else None
    if thumbnail_file_id:
        thumbnail_info = context.bot.get_file(thumbnail_file_id)
        thumbnail_path = os.path.join(SAVE_PATH, f"{file_id}_thumbnail.jpg")
        thumbnail_info.download(thumbnail_path)

        # Save thumbnail information to MongoDB
        user_collection.update_one({'_id': user_id}, {'$set': {'thumbnail_path': thumbnail_path}}, upsert=True)

    file_info.download(file_local_path)

  # Check if user has pending files
        if user_id in self.pending_files:
            self.pending_files[user_id].append(file_local_path)
            files_count = len(self.pending_files[user_id])
            update.message.reply_text(f'File {files_count} of 10 received.')

    # Check if it's time to merge
            if files_count >= 10:
                self.merge_files(user_id, update.message.chat_id)
              else:
            self.pending_files[user_id] = [file_local_path]
            update.message.reply_text('File 1 of 10 received. Send more files to merge.')

    def merge_files(self, user_id, chat_id):
        if user_id in self.pending_files:
            file_paths = self.pending_files[user_id]
            merged_file_path = os.path.join(SAVE_PATH, f"merged_{user_id}.mkv")

            # Use mkvtoolnix to merge files
            subprocess.run([os.path.join(MKVTOOLNIX_PATH, 'mkvmerge'), '-o', merged_file_path] + file_paths)

            context.bot.send_message(chat_id=chat_id, text='Files merged successfully. 📦')
            context.bot.send_document(chat_id=chat_id, document=open(merged_file_path, 'rb'))

            # Clean up
            for file_path in file_paths:
                os.remove(file_path)
            self.pending_files.pop(user_id, None)

def cancel(self, update: Update, context: CallbackContext) -> None:
        user_id = update.message.from_user.id

        if user_id in self.pending_files:
            self.pending_files.pop(user_id, None)
            update.message.reply_text('Operation canceled. You can start a new one.')

    # Add metadata editing button
    keyboard = [[InlineKeyboardButton("Edit Metadata 📝", callback_data='edit_metadata')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(f'File saved as: {new_filename}', reply_markup=reply_markup)

def delete_thumbnail(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user_data = user_collection.find_one({'_id': user_id})

    if user_data and 'thumbnail_path' in user_data:
        thumbnail_path = user_data['thumbnail_path']
        os.remove(thumbnail_path)
        user_collection.update_one({'_id': user_id}, {'$unset': {'thumbnail_path': ""}})  # Remove thumbnail path from MongoDB
        update.message.reply_text("Thumbnail deleted successfully. 🗑️")
    else:
        update.message.reply_text("No thumbnail found.")

def show_thumbnail(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user_data = user_collection.find_one({'_id': user_id})

    if user_data and 'thumbnail_path' in user_data:
        thumbnail_path = user_data['thumbnail_path']
        context.bot.send_photo(chat_id=update.message.chat_id, photo=open(thumbnail_path, 'rb'))
    else:
        update.message.reply_text("No thumbnail found.")

def edit_metadata(update: Update, context: CallbackContext) -> None:
    user_id = update.callback_query.from_user.id
    user_data = user_collection.find_one({'_id': user_id})

    if user_data and 'thumbnail_path' in user_data:
        thumbnail_path = user_data['thumbnail_path']
        context.bot.send_photo(chat_id=update.callback_query.message.chat_id, photo=open(thumbnail_path, 'rb'))
        context.bot.send_message(chat_id=update.callback_query.message.chat_id, text='Editing metadata...')

        video_file_path = os.path.join(SAVE_PATH, f"{user_data['_id']}.mp4")
        subprocess.run(['ffmpeg', '-i', user_data['file_path'], video_file_path])

        # Edit video title, audio name, and subtitles name using FFmpeg
        subprocess.run(['ffmpeg', '-i', video_file_path, '-metadata', 'title=NewTitle', '-c', 'copy', '-y', video_file_path])

        # Example: Extract audio and save it with a new name
        audio_file_path = os.path.join(SAVE_PATH, f"{user_data['_id']}_audio.mp3")
        subprocess.run(['ffmpeg', '-i', video_file_path, '-vn', '-acodec', 'libmp3lame', audio_file_path])

        # Example: Extract subtitles and save them with a new name
        subtitle_file_path = os.path.join(SAVE_PATH, f"{user_data['_id']}_subtitles.srt")
        subprocess.run(['ffmpeg', '-i', video_file_path, subtitle_file_path])

        context.bot.send_message(chat_id=update.callback_query.message.chat_id, text='Metadata edited successfully. 📝')

    else:
        update.callback_query.edit_message_text("No thumbnail found.")

def check_status(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    if str(user_id) == OWNER_ID:  # Replace OWNER_ID with your Telegram user ID
        context.bot.send_message(chat_id=update.message.chat_id, text='Bot is active and running. ✅')
    else:
        context.bot.send_message(chat_id)
                                 
                                 def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    shell_bot = shellBot()

    dp.add_handler(CommandHandler("start", shell_bot.start))
    dp.add_handler(MessageHandler(Filters.document, shell_bot.handle_file))
    dp.add_handler(CommandHandler("deletethumbnail", shell_bot.delete_thumbnail))
    dp.add_handler(CommandHandler("showthumbnail", shell_bot.show_thumbnail))
    dp.add_handler(CallbackQueryHandler(shell_bot.edit_metadata, pattern='^edit_metadata$'))
    dp.add_handler(CommandHandler("status", shell_bot.check_status))
    dp.add_handler(CommandHandler("cancel", shell_bot.cancel))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

                               
