from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ConversationHandler, ContextTypes

from utils.config import sql_connection
from utils.logger import get_logger
from utils.chatting import safe_chat
from db import set_user_forward_address, is_password_set, check_password_match
from telegram.ext import MessageHandler, filters

class SetRecipient():
    def __init__(self,  
                 update,
                 context,
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
        
        try:
            # Wait for text message
            update = await self.context.application.update_queue.get()
            
            # If it's a text message
            if update.message and update.message.text:
                return await self.handle_code(update, self.context)
                
        except Exception as e:
            self.logger.error(f"Error waiting for recipient code: {e}")
            await safe_chat(self.context, self.chat_id, "An error occurred. Please try again.")
            return ConversationHandler.END

    async def handle_code(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        address = update.message.text

        if is_password_set(self.sql_connection, address):
            for attempt in range(3):
                await safe_chat(context, self.chat_id, "Please enter the password:")
                try:
                    pwd_update = await context.application.update_queue.get()
                    if pwd_update.message and pwd_update.message.text:
                        password = pwd_update.message.text
                        if check_password_match(self.sql_connection, address, password):
                            break
                        else:
                            if attempt < 2:
                                await safe_chat(context, self.chat_id, "Incorrect password. Please try again.")
                            else:
                                await safe_chat(context, self.chat_id, "Maximum password attempts reached.")
                                return ConversationHandler.END
                except Exception as e:
                    self.logger.error(f"Error processing password: {e}")
                    await safe_chat(context, self.chat_id, "An error occurred. Please try again.")
                    return ConversationHandler.END
        
        try:
            result = set_user_forward_address(self.sql_connection, self.user_id, address)
        except Exception as e:
            self.logger.error(f"Error setting recipient: {e}")
            await safe_chat(context, self.chat_id, str(e))
            return ConversationHandler.END
        
        await safe_chat(context, self.chat_id, "Code accepted! You can now start sending song requests using the /biisitoive command.")
        return ConversationHandler.END