from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from utils.chatting import safe_chat
from utils.logger import get_logger
from utils.config import sql_connection

class SongRequest:
    def __init__(self, 
                 context, 
                 update, 
                 recipient,
                 sender_id,
                 sender_nickname = "Unknown",
                 sql_connection = sql_connection):
        self.context = context
        self.update = update
        self.recipient = recipient
        self.sender_nickname = sender_nickname
        self.sql_connection = sql_connection
        self.song_name_value = None
        self.artist_name_value = None
        self.logger = get_logger(__name__)
        self.sender_id = sender_id
        self.chat_id = update.effective_chat.id

    async def process_request(self):
        await safe_chat(self.context, self.update.effective_chat.id, "What's the name of the song?")
        while True:
            update = await self.context.application.update_queue.get()
            if update.effective_chat.id == self.chat_id:
                return await self.song_name(update, self.context)

    async def song_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.song_name_value = update.message.text
        await safe_chat(context, update.effective_chat.id, "Who's the artist?")
        while True:
            update = await self.context.application.update_queue.get()
            if update.effective_chat.id == self.chat_id:
                return await self.artist_name(update, self.context)

    async def artist_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.artist_name_value = update.message.text
        keyboard = [[InlineKeyboardButton("Skip notes", callback_data='skip_notes')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_chat(context, update.effective_chat.id, 
                       "Add any notes about your request (max 150 characters) or click Skip:", 
                       reply_markup=reply_markup)
        while True:
            update = await self.context.application.update_queue.get()
            if update.effective_chat.id == self.chat_id:
                return await self.notes(update, self.context)

    async def notes(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            if query.data == 'skip_notes':
                self.notes = ""
                return await self.show_confirmation(update, self.context)
        
        if len(update.message.text) > 150:
            await safe_chat(context, update.effective_chat.id, 
                          "Notes too long! Please keep it under 150 characters. Try again:")
            while True:
                update = await self.context.application.update_queue.get()
                if update.effective_chat.id == self.chat_id:
                    return await self.notes(update, self.context)
        
        self.notes = update.message.text
        return await self.show_confirmation(update, self.context)

    async def show_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [[InlineKeyboardButton("Yes", callback_data='yes'),
                    InlineKeyboardButton("No", callback_data='no')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        confirm_text = f"Confirm song request:\nSong: {self.song_name_value}\nArtist: {self.artist_name_value}"
        if self.notes:
            confirm_text += f"\nNotes: {self.notes}"
        await safe_chat(context, update.effective_chat.id, confirm_text, reply_markup=reply_markup)
        while True:
            update = await self.context.application.update_queue.get()
            if update.effective_chat.id == self.chat_id:
                return await self.confirm(update, self.context)

    async def confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        if query.data == 'yes':
            message = f"New song request from {self.sender_nickname}!\nSong: {self.song_name_value}\nArtist: {self.artist_name_value}\nNotes: {self.notes}"
            await safe_chat(context, self.recipient, message)
            await safe_chat(context, update.effective_chat.id, "Song request sent!")
            self.logger.info(f"Song request from {self.sender_id} sent to {self.recipient}")
            return ConversationHandler.END
        else:
            await safe_chat(context, update.effective_chat.id, "Song request cancelled.")
            self.logger.info(f"Song request from {self.sender_id} cancelled")
            return ConversationHandler.END
