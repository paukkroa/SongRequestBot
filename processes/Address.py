from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler
from datetime import timezone, timedelta, datetime
import random
import string
import hashlib

from utils.chatting import safe_chat
from utils.config import sql_connection
from utils.logger import get_logger
from db.recipient_queries import *

class NewAddress():
    def __init__(self, 
                 context, 
                 update,
                 recipient,
                 sql_connection = sql_connection):
        self.context = context
        self.update = update
        self.recipient = recipient
        self.sql_connection = sql_connection
        self.logger = get_logger(__name__)

    async def process_request(self):
        keyboard = [
            [InlineKeyboardButton("Custom", callback_data='custom'),
             InlineKeyboardButton("Random", callback_data='random')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_chat(self.context, self.update.effective_chat.id,
                       "Do you want to use a custom code or a randomly generated one?",
                       reply_markup)
        
        update = await self.context.application.update_queue.get()
        query = update.callback_query
        
        if query.data == 'custom':
            await safe_chat(self.context, update.effective_chat.id, "Please send your preferred code:")
            update = await self.context.application.update_queue.get()
            address = update.message.text
            
            while get_address_attributes(self.sql_connection, address) is not None:
                await safe_chat(self.context, update.effective_chat.id,
                              "This code is already in use. Please choose another one:")
                update = await self.context.application.update_queue.get()
                address = update.message.text
        else:
            while True:
                address = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
                if get_address_attributes(self.sql_connection, address) is None:
                    break

        # Ask validity period
        keyboard = [[
            InlineKeyboardButton("1 day", callback_data='1d'),
            InlineKeyboardButton("3 days", callback_data='3d'),
            InlineKeyboardButton("7 days", callback_data='7d'),
            InlineKeyboardButton("30 days", callback_data='30d'),
            InlineKeyboardButton("Indefinitely", callback_data='inf'),
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_chat(self.context, update.effective_chat.id,
                       "How long should the code be valid?",
                       reply_markup)
        
        update = await self.context.application.update_queue.get()
        query = update.callback_query
        days_map = {'1d': 1, '3d': 3, '7d': 7, '30d': 30, 'inf': 365000}  # ~1000 years
        validity_period = query.data
        days = days_map[query.data]
        valid_until = (datetime.now(timezone.utc) + timedelta(days=days_map[query.data])).strftime('%Y-%m-%d %H:%M:%S')
        if validity_period == 'inf':
            valid_until = None


        # Ask for password
        keyboard = [[
            InlineKeyboardButton("Yes", callback_data='yes_pwd'),
            InlineKeyboardButton("No", callback_data='no_pwd')
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_chat(self.context, update.effective_chat.id,
                       "Would you like to set a password?",
                       reply_markup)
        
        update = await self.context.application.update_queue.get()
        query = update.callback_query
        
        password = None
        if query.data == 'yes_pwd':
            await safe_chat(self.context, update.effective_chat.id, "Please send the password:")
            update = await self.context.application.update_queue.get()
            password = update.message.text
            hashed_password = hashlib.sha256(password.encode()).hexdigest()

        # Create address
        chat_id = update.effective_chat.id

        self.logger.info(f"Creating new address {address} for recipient {self.recipient}.")
        create_new_address(self.sql_connection, address, self.recipient, hashed_password, valid_until)
        
        msg = f"Address created successfully!\nCode: {address}\n"
        if validity_period != 'inf':
            msg += f"Valid for {days} days."
        if password:
            msg += f"\nPassword: {password}"
        
        await safe_chat(self.context, chat_id, msg)

class ExpireAddress():
    def __init__(self, 
                 context, 
                 update,
                 chat_id,
                 sql_connection = sql_connection):
        self.context = context
        self.update = update
        self.chat_id = chat_id
        self.sql_connection = sql_connection
        self.logger = get_logger(__name__)

    async def process_request(self):
        addresses = list_valid_recipient_addresses(self.sql_connection, self.chat_id)
        
        if not addresses:
            await safe_chat(self.context, self.chat_id, "You don't have any addresses set.")
            return ConversationHandler.END
        
        keyboard = [[InlineKeyboardButton(addr, callback_data=addr)] for addr in addresses]
        keyboard.append([InlineKeyboardButton("Exit", callback_data='exit')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await safe_chat(self.context, self.chat_id, "Select address to be expired:", reply_markup)
        
        update = await self.context.application.update_queue.get()
        return await self.handle_address_selection(update, self.context)

    async def handle_address_selection(self, update, context):
        query = update.callback_query
        if query.data == 'exit':
            await safe_chat(context, update.effective_chat.id, "Operation cancelled.")
            return ConversationHandler.END
        
        context.user_data['address_to_delete'] = query.data
        keyboard = [[
            InlineKeyboardButton("Yes", callback_data='yes_delete'),
            InlineKeyboardButton("No", callback_data='no_delete')
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_chat(context, update.effective_chat.id, 
                        f"Are you sure you want to expire address {query.data}?",
                        reply_markup)
        
        update = await self.context.application.update_queue.get()
        return await self.handle_confirm_delete(update, context)

    async def handle_confirm_delete(self, update, context):
        query = update.callback_query
        if query.data == 'yes_delete':
            address = context.user_data['address_to_delete']
            expire_address(self.sql_connection, address)
            await safe_chat(context, update.effective_chat.id, f"Address {address} expired successfully.")
        else:
            await safe_chat(context, update.effective_chat.id, "Operation cancelled.")
        return ConversationHandler.END
       

class ToggleAddress():
    def __init__(self, 
                 context, 
                 update,
                 chat_id,
                 sql_connection = sql_connection):
        self.context = context
        self.update = update
        self.chat_id = chat_id
        self.sql_connection = sql_connection
        self.logger = get_logger(__name__)

    async def process_request(self):
        addresses = list_valid_recipient_addresses(self.sql_connection, self.chat_id)
        
        if not addresses:
            await safe_chat(self.context, self.chat_id, "You don't have any addresses set.")
            return ConversationHandler.END
        
        keyboard = [[InlineKeyboardButton(addr, callback_data=addr)] for addr in addresses]
        keyboard.append([InlineKeyboardButton("Exit", callback_data='exit')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await safe_chat(self.context, self.chat_id, "Select address to toggle:", reply_markup)
        
        update = await self.context.application.update_queue.get()
        query = update.callback_query
        
        if query.data == 'exit':
            await safe_chat(self.context, update.effective_chat.id, "Operation cancelled.")
            return ConversationHandler.END
        
        try:
            toggle_success = toggle_active(self.sql_connection, query.data)
            if toggle_success:
                await safe_chat(self.context, update.effective_chat.id, f"Address {query.data} toggled successfully.")
        except Exception as e:
            self.logger.error(f"Error toggling address: {e}")
            await safe_chat(self.context, update.effective_chat.id, str(e))
        
        return ConversationHandler.END
    
class ReleaseAddress():
    def __init__(self, 
                 context, 
                 update,
                 chat_id,
                 sql_connection = sql_connection):
        self.context = context
        self.update = update
        self.chat_id = chat_id
        self.sql_connection = sql_connection
        self.logger = get_logger(__name__)

    async def process_request(self):
        addresses = list_recipient_addresses(self.sql_connection, self.chat_id)
        
        if not addresses:
            await safe_chat(self.context, self.chat_id, "You don't have any addresses set.")
            return ConversationHandler.END
        
        keyboard = [[InlineKeyboardButton(addr, callback_data=addr)] for addr in addresses]
        keyboard.append([InlineKeyboardButton("Exit", callback_data='exit')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await safe_chat(self.context, self.chat_id, "Select address to be released:", reply_markup)
        
        update = await self.context.application.update_queue.get()
        return await self.handle_address_selection(update, self.context)

    async def handle_address_selection(self, update, context):
        query = update.callback_query
        if query.data == 'exit':
            await safe_chat(context, update.effective_chat.id, "Operation cancelled.")
            return ConversationHandler.END
        
        context.user_data['address_to_delete'] = query.data
        keyboard = [[
            InlineKeyboardButton("Yes", callback_data='yes_delete'),
            InlineKeyboardButton("No", callback_data='no_delete')
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_chat(context, update.effective_chat.id, 
                        f"Are you sure you want to release address {query.data}?",
                        reply_markup)
        
        update = await self.context.application.update_queue.get()
        return await self.handle_confirm_delete(update, context)

    async def handle_confirm_delete(self, update, context):
        query = update.callback_query
        if query.data == 'yes_delete':
            address = context.user_data['address_to_delete']
            release_address(self.sql_connection, address)
            await safe_chat(context, update.effective_chat.id, f"Address {address} released successfully.")
        else:
            await safe_chat(context, update.effective_chat.id, "Operation cancelled.")
        return ConversationHandler.END