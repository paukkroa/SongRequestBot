from telegram import Update
from telegram.ext import ContextTypes

from db.recipient_queries import add_new_recipient, get_recipient_chat_id, get_address, create_new_address
from db.user_queries import add_user
from utils.chatting import safe_chat
from processes import NewAddress, DeleteAddress

async def register_recipient(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Register a new recipient"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type

    # Add user
    add_user(user_id, role='recipient')

    # Add recipient chat
    add_new_recipient(user_id, chat_id, chat_type)

async def create_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create a new address for the recipient"""
    chat_id = update.effective_chat.id

    # check if the recipient chat exists
    recipient_chat_id = get_recipient_chat_id(chat_id)
    if recipient_chat_id is None:
        await safe_chat(context, chat_id, "You need to register before creating an address.")
        return
    
    # Create a new address
    new_address = NewAddress(context, update, recipient_chat_id)
    await new_address.process_request()

async def remove_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove an address from the recipient"""
    chat_id = update.effective_chat.id

    # check if the recipient chat exists
    recipient_chat_id = get_recipient_chat_id(chat_id)
    if recipient_chat_id is None:
        await safe_chat(context, chat_id, "You need to register before removing an address.")
        return

    # Start removal process
    address_removal = DeleteAddress(context, update, recipient_chat_id)
    await address_removal.process_request()