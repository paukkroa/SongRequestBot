from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from utils.chatting import safe_chat
from utils.logger import get_logger

class SongRequest:
    def __init__(self, 
                 context, 
                 update, 
                 recipient,
                 sender_nickname = "Unknown"):
        self.context = context
        self.update = update
        self.recipient = recipient
        self.sender_nickname = sender_nickname
        self.song_name = None
        self.artist_name = None
        self.logger = get_logger(__name__)
        self.sender_id = update.effective_user.id

    SONG_NAME, ARTIST_NAME, NOTES, CONFIRMATION = range(4)

    async def process_request(self):
        await safe_chat(self.context, self.update.effective_chat.id, "What's the name of the song?")
        return self.SONG_NAME

    async def song_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.song_name = update.message.text
        await safe_chat(context, update.effective_chat.id, "Who's the artist?")
        return self.ARTIST_NAME

    async def artist_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.artist_name = update.message.text
        keyboard = [[InlineKeyboardButton("Skip notes", callback_data='skip_notes')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_chat(context, update.effective_chat.id, 
                       "Add any notes about your request (max 150 characters) or click Skip:", 
                       reply_markup=reply_markup)
        return self.NOTES

    async def notes(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            if query.data == 'skip_notes':
                self.notes = ""
                return await self.show_confirmation(update, context)
        
        if len(update.message.text) > 150:
            await safe_chat(context, update.effective_chat.id, 
                          "Notes too long! Please keep it under 150 characters. Try again:")
            return self.NOTES
        
        self.notes = update.message.text
        return await self.show_confirmation(update, context)

    async def show_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [[InlineKeyboardButton("Yes", callback_data='yes'),
                    InlineKeyboardButton("No", callback_data='no')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        confirm_text = f"Confirm song request:\nSong: {self.song_name}\nArtist: {self.artist_name}"
        if self.notes:
            confirm_text += f"\nNotes: {self.notes}"
        await safe_chat(context, update.effective_chat.id, confirm_text, reply_markup=reply_markup)
        return self.CONFIRMATION

    async def confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        if query.data == 'yes':
            message = f"New song request from {self.sender_nickname}!\nSong: {self.song_name}\nArtist: {self.artist_name}"
            await safe_chat(context, self.recipient, message)
            await safe_chat(context, update.effective_chat.id, "Song request sent!")
            self.logger.info(f"Song request from {self.sender_id} sent to {self.recipient}")
            return ConversationHandler.END
        else:
            await safe_chat(context, update.effective_chat.id, "Song request cancelled.")
            self.logger.info(f"Song request from {self.sender_id} cancelled")
            return ConversationHandler.END
