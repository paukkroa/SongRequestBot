from telegram import Update
from telegram.ext import ContextTypes

from db.recipient_queries import add_new_recipient, get_recipient_chat_id, get_recipient_addresses
from db.user_queries import add_user
from utils.chatting import safe_chat
from processes import NewAddress, ExpireAddress, ToggleAddress, ReleaseAddress
from utils.config import sql_connection

async def register_recipient(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Register a new recipient"""
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    chat_name = update.effective_chat.title

    # Add user
    # add_user(sql_connection, user_id, nickname='recipient' role='recipient')

    # Add recipient chat
    result = add_new_recipient(sql_connection, chat_id, chat_type)
    if not result:
        await safe_chat(context, chat_id, f"This chat ({chat_name}) has already been registered as a recipient!")
        return
    else:
        await safe_chat(context, chat_id, f"Success! This chat ({chat_name}) can now receive song requests. You can now create a song request code with /uusi.")

async def create_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create a new address for the recipient"""
    chat_id = update.effective_chat.id

    # check if the recipient chat exists
    recipient_exists = get_recipient_chat_id(sql_connection, chat_id)
    if not recipient_exists:
        await safe_chat(context, chat_id, "You need to register before creating an address.")
        return
    
    # Create a new address
    new_address = NewAddress(context, update, chat_id, sql_connection)
    await new_address.process_request()

async def remove_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove an address from the recipient"""
    chat_id = update.effective_chat.id

    # check if the recipient chat exists
    recipient_exists = get_recipient_chat_id(sql_connection, chat_id)
    if not recipient_exists:
        await safe_chat(context, chat_id, "You need to register before creating an address.")
        return
    

    # Start removal process
    address_removal = ExpireAddress(context, update, chat_id, sql_connection)
    await address_removal.process_request()

async def list_addresses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all addresses for the recipient"""
    chat_id = update.effective_chat.id

    # check if the recipient chat exists
    recipient_chat_id = get_recipient_chat_id(sql_connection, chat_id)
    if not recipient_chat_id:
        await safe_chat(context, chat_id, "You need to register before listing addresses.")
        return

    # Get all addresses
    addresses = get_recipient_addresses(sql_connection, chat_id)
    if not addresses:
        await safe_chat(context, chat_id, "You don't have any addresses.")
        return

    # Send addresses
    await safe_chat(context, chat_id, addresses)

async def toggle_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle an address for the recipient"""
    chat_id = update.effective_chat.id

    # check if the recipient chat exists
    recipient_chat_id = get_recipient_chat_id(sql_connection, chat_id)
    if not recipient_chat_id:
        await safe_chat(context, chat_id, "You need to register before toggling addresses.")
        return

    # Start toggle process
    toggle = ToggleAddress(context, update, chat_id, sql_connection)
    await toggle.process_request()

async def release_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Release an address (delete from database)"""
    chat_id = update.effective_chat.id

    # check if the recipient chat exists
    recipient_chat_id = get_recipient_chat_id(sql_connection, chat_id)
    if not recipient_chat_id:
        await safe_chat(context, chat_id, "You need to register before releasing addresses.")
        return

    # Start removal process
    address_removal = ReleaseAddress(context, update, chat_id, sql_connection)
    await address_removal.process_request()