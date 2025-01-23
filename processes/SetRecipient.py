from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ConversationHandler, ContextTypes

from utils.config import sql_connection
from utils.logger import get_logger
from utils.chatting import safe_chat
from db import set_user_forward_address

class SetRecipient():
    def __init__(self, 
                 context, 
                 update,
                 user_id,
                 chat_id,
                 sql_connection = sql_connection):
        self.context = context
        self.update = update
        self.user_id = user_id
        self.chat_id = chat_id
        self.sql_connection = sql_connection
        self.logger = get_logger(__name__)

    async def process_request(self):
        await safe_chat(self.context, self.chat_id, "Please provide the recipient code:")
        return self.handle_code

    async def handle_code(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        address = update.message.text
        
        try:
            result = set_user_forward_address(self.sql_connection, self.user_id, address)
        except Exception as e:
            self.logger.error(f"Error setting recipient: {e}")
            await safe_chat(context, self.chat_id, e)
            return ConversationHandler.END
        
        await safe_chat(context, self.chat_id, "Code accepted! You can now start sending song requests using the /biisitoive command.")
        return ConversationHandler.END