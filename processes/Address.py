from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler
from datetime import datetime, timedelta
import random
import string
import hashlib

from utils.chatting import safe_chat
from db.recipient_queries import create_new_address, get_address_attributes, remove_address, get_recipient_addresses

class NewAddress():
    def __init__(self, 
                 context, 
                 update,
                 recipient):
        self.context = context
        self.update = update
        self.recipient = recipient

    async def process_request(self, update, context):
        keyboard = [
            [InlineKeyboardButton("Custom address", callback_data='custom'),
             InlineKeyboardButton("Random address", callback_data='random')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_chat(context, update.effective_chat.id,
                       "Do you want to use a custom address or a randomly generated one?",
                       reply_markup)

    async def handle_address_type(self, update, context):
        query = update.callback_query
        if query.data == 'custom':
            await safe_chat(context, update.effective_chat.id, "Please send your custom address:")
            return 'WAITING_CUSTOM_ADDRESS'
        else:
            while True:
                address = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
                if get_address_attributes(address) is None:
                    break
            context.user_data['address'] = address
            await self.ask_validity_period(update, context)
            return 'WAITING_VALIDITY'

    async def handle_custom_address(self, update, context):
        address = update.message.text
        if get_address_attributes(address) is not None:
            await safe_chat(context, update.effective_chat.id,
                          "This address already exists. Please choose another one:")
            return 'WAITING_CUSTOM_ADDRESS'
        context.user_data['address'] = address
        await self.ask_validity_period(update, context)
        return 'WAITING_VALIDITY'

    async def ask_validity_period(self, update, context):
        keyboard = [[
            InlineKeyboardButton("1 day", callback_data='1d'),
            InlineKeyboardButton("3 days", callback_data='3d'),
            InlineKeyboardButton("7 days", callback_data='7d'),
            InlineKeyboardButton("30 days", callback_data='30d')
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_chat(context, update.effective_chat.id,
                       "How long should the address be valid?",
                       reply_markup)

    async def handle_validity(self, update, context):
        query = update.callback_query
        days_map = {'1d': 1, '3d': 3, '7d': 7, '30d': 30}
        valid_until = datetime.now() + timedelta(days=days_map[query.data])
        context.user_data['valid_until'] = valid_until
        
        keyboard = [[
            InlineKeyboardButton("Yes", callback_data='yes_pwd'),
            InlineKeyboardButton("No", callback_data='no_pwd')
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_chat(context, update.effective_chat.id,
                       "Would you like to set a password?",
                       reply_markup)
        return 'WAITING_PASSWORD_CHOICE'

    async def handle_password_choice(self, update, context):
        query = update.callback_query
        if query.data == 'yes_pwd':
            await safe_chat(context, update.effective_chat.id, "Please send the password:")
            return 'WAITING_PASSWORD'
        else:
            await self.finalize_address(update, context, None)
            return ConversationHandler.END

    async def handle_password(self, update, context):
        password = update.message.text
        password = hashlib.sha256(password.encode()).hexdigest()
        await self.finalize_address(update, context, password)
        return ConversationHandler.END

    async def finalize_address(self, update, context, password):
        address = context.user_data['address']
        valid_until = context.user_data['valid_until']
        chat_id = update.effective_chat.id
        create_new_address(address, chat_id, password, 1, valid_until)
        
        msg = f"Address created successfully!\nAddress: {address}\nValid until: {valid_until.strftime('%Y-%m-%d %H:%M:%S')}"
        if password:
            msg += f"\nPassword: {password}"
        
        await safe_chat(context, chat_id, msg)

class DeleteAddress():
    def __init__(self, 
                 context, 
                 update):
        self.context = context
        self.update = update

    async def process_request(self, update, context):
        chat_id = update.effective_chat.id
        addresses = get_recipient_addresses(chat_id)
        
        if not addresses:
            await safe_chat(context, chat_id, "You don't have any addresses set.")
            return ConversationHandler.END
        
        keyboard = [[InlineKeyboardButton(addr, callback_data=addr)] for addr in addresses]
        keyboard.append([InlineKeyboardButton("Exit", callback_data='exit')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await safe_chat(context, chat_id, "Select address to delete:", reply_markup)
        return 'WAITING_ADDRESS_SELECTION'

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
                        f"Are you sure you want to delete address {query.data}?",
                        reply_markup)
        return 'CONFIRM_DELETE'

    async def handle_confirm_delete(self, update, context):
        query = update.callback_query
        if query.data == 'yes_delete':
            address = context.user_data['address_to_delete']
            remove_address(address)
            await safe_chat(context, update.effective_chat.id, f"Address {address} deleted successfully.")
        else:
            await safe_chat(context, update.effective_chat.id, "Operation cancelled.")
        return ConversationHandler.END
       