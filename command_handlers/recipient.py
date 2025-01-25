from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)
import random
import string
import hashlib

from db.recipient_queries import *
from utils.chatting import safe_chat
from utils.config import sql_connection
from datetime import datetime, timezone, timedelta

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

# Define states
CHOOSE_TYPE, ENTER_CUSTOM, CHOOSE_VALIDITY, CHOOSE_PASSWORD, ENTER_PASSWORD, PROCESS_ADDRESS = 30, 31, 32, 33, 34, 35

async def create_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create a new address for the recipient"""
    chat_id = update.effective_chat.id

    # check if the recipient chat exists
    recipient_exists = get_recipient_chat_id(sql_connection, chat_id)
    if not recipient_exists:
        await safe_chat(context, chat_id, "You need to register before creating an address.")
        return ConversationHandler.END
    
    # check how many addresses the recipient owns already
    address_count = get_amount_of_recipient_addresses(sql_connection, chat_id)
    if address_count >= 5:
        await safe_chat(context, chat_id, "You can only have 5 addresses at a time. Release some before creating new ones.")
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton("Custom", callback_data='custom'),
         InlineKeyboardButton("Random", callback_data='random')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await safe_chat(context, chat_id,
                   "Do you want to use a custom code or a randomly generated one?",
                   reply_markup)
    return CHOOSE_TYPE

async def type_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'custom':
        await safe_chat(context, update.effective_chat.id, "Please send your preferred code:")
        return ENTER_CUSTOM
    else:
        while True:
            address = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            if get_address_attributes(sql_connection, address) is None:
                context.user_data['address'] = address
                break
        return await ask_validity(update, context)

async def handle_custom_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    address = update.message.text
    if get_address_attributes(sql_connection, address) is not None:
        await safe_chat(context, update.effective_chat.id,
                       "This code is already in use. Please choose another one:")
        return ENTER_CUSTOM
    
    context.user_data['address'] = address
    return await ask_validity(update, context)

async def ask_validity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[
        InlineKeyboardButton("1 day", callback_data='1d'),
        InlineKeyboardButton("3 days", callback_data='3d'),
        InlineKeyboardButton("7 days", callback_data='7d'),
        InlineKeyboardButton("30 days", callback_data='30d'),
        InlineKeyboardButton("Indefinitely", callback_data='inf'),
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await safe_chat(context, update.effective_chat.id,
                   "How long should the code be valid?",
                   reply_markup)
    return CHOOSE_VALIDITY

async def handle_validity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    days_map = {'1d': 1, '3d': 3, '7d': 7, '30d': 30, 'inf': 365000}
    validity_period = query.data
    days = days_map[validity_period]
    
    if validity_period == 'inf':
        context.user_data['valid_until'] = None
    else:
        context.user_data['valid_until'] = (datetime.now(timezone.utc) + 
                                          timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
    
    keyboard = [[
        InlineKeyboardButton("Yes", callback_data='yes_pwd'),
        InlineKeyboardButton("No", callback_data='no_pwd')
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await safe_chat(context, update.effective_chat.id,
                   "Would you like to set a password?",
                   reply_markup)
    return CHOOSE_PASSWORD

async def handle_password_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'yes_pwd':
        await safe_chat(context, update.effective_chat.id, "Please send the password:")
        return ENTER_PASSWORD
    else:
        context.user_data['password'] = None
        return await finalize_address(update, context)

async def handle_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text
    context.user_data['password'] = password
    return await finalize_address(update, context)

async def finalize_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    address = context.user_data['address']
    valid_until = context.user_data['valid_until']
    password = context.user_data['password']
    
    hashed_password = (hashlib.sha256(password.encode()).hexdigest() 
                      if password else None)
    
    create_new_address(sql_connection, address, chat_id, hashed_password, valid_until)
    
    msg = f"Address created successfully!\nCode: {address}\n"
    if valid_until:
        msg += f"Valid until: {valid_until}"
    if password:
        msg += f"\nPassword: {password}"
    
    await safe_chat(context, chat_id, msg)
    return ConversationHandler.END

# Create conversation handler
def get_create_address_conv_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("uusi", create_address)],  # Simplified filter
        states={
            CHOOSE_TYPE: [CallbackQueryHandler(type_choice)],
            ENTER_CUSTOM: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_code)],
            CHOOSE_VALIDITY: [CallbackQueryHandler(handle_validity)],
            CHOOSE_PASSWORD: [CallbackQueryHandler(handle_password_choice)],
            ENTER_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_password)]
        },
        fallbacks=[],
        conversation_timeout=300,  # 5 minutes
        per_user=True,
        per_chat=True
    )

# Define states for remove address conversation
CHOOSE_ADDRESS, CONFIRM_DELETE = 40, 41

async def remove_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove an address from the recipient"""
    chat_id = update.effective_chat.id

    # check if the recipient chat exists
    recipient_exists = get_recipient_chat_id(sql_connection, chat_id)
    if not recipient_exists:
        await safe_chat(context, chat_id, "You need to register before removing an address.")
        return ConversationHandler.END

    addresses = list_valid_recipient_addresses(sql_connection, chat_id)
    if not addresses:
        await safe_chat(context, chat_id, "You don't have any addresses set.")
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton(addr, callback_data=addr)] for addr in addresses]
    keyboard.append([InlineKeyboardButton("Exit", callback_data='exit')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await safe_chat(context, chat_id, "Select address to be expired:", reply_markup)
    return CHOOSE_ADDRESS

async def handle_address_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
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
    return CONFIRM_DELETE

async def handle_confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'yes_delete':
        address = context.user_data['address_to_delete']
        expire_address(sql_connection, address)
        await safe_chat(context, update.effective_chat.id, f"Address {address} expired successfully.")
    else:
        await safe_chat(context, update.effective_chat.id, "Operation cancelled.")
    return ConversationHandler.END

def get_remove_address_conv_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("poista", remove_address, filters.ChatType.GROUPS | filters.ChatType.PRIVATE)],
        states={
            CHOOSE_ADDRESS: [CallbackQueryHandler(handle_address_selection)],
            CONFIRM_DELETE: [CallbackQueryHandler(handle_confirm_delete)]
        },
        fallbacks=[],
        conversation_timeout=300,  # 5 minutes
        per_user=True,
        per_chat=True
    )

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

# Define states for toggle address conversation
TOGGLE_CHOOSE_ADDRESS = 50

async def toggle_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle an address for the recipient"""
    chat_id = update.effective_chat.id

    # check if the recipient chat exists
    recipient_chat_id = get_recipient_chat_id(sql_connection, chat_id)
    if not recipient_chat_id:
        await safe_chat(context, chat_id, "You need to register before toggling addresses.")
        return ConversationHandler.END

    addresses = list_valid_recipient_addresses(sql_connection, chat_id)
    if not addresses:
        await safe_chat(context, chat_id, "You don't have any addresses set.")
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton(addr, callback_data=addr)] for addr in addresses]
    keyboard.append([InlineKeyboardButton("Exit", callback_data='exit')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await safe_chat(context, chat_id, "Select address to toggle:", reply_markup)
    return TOGGLE_CHOOSE_ADDRESS

async def handle_toggle_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'exit':
        await safe_chat(context, update.effective_chat.id, "Operation cancelled.")
        return ConversationHandler.END
    
    try:
        toggle_success = toggle_active(sql_connection, query.data)
        if toggle_success:
            await safe_chat(context, update.effective_chat.id, 
                          f"Address {query.data} toggled successfully.")
    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"Error toggling address: {e}")
        await safe_chat(context, update.effective_chat.id, str(e))
    
    return ConversationHandler.END

def get_toggle_address_conv_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("onoff", toggle_address, filters.ChatType.GROUPS | filters.ChatType.PRIVATE)],
        states={
            TOGGLE_CHOOSE_ADDRESS: [CallbackQueryHandler(handle_toggle_selection)]
        },
        fallbacks=[],
        conversation_timeout=300,  # 5 minutes
        per_user=True,
        per_chat=True
    )

# Define states for release address conversation
RELEASE_CHOOSE_ADDRESS, RELEASE_CONFIRM = 60, 61

async def release_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Release an address (delete from database)"""
    chat_id = update.effective_chat.id

    # check if the recipient chat exists
    recipient_chat_id = get_recipient_chat_id(sql_connection, chat_id)
    if not recipient_chat_id:
        await safe_chat(context, chat_id, "You need to register before releasing addresses.")
        return ConversationHandler.END

    addresses = list_recipient_addresses(sql_connection, chat_id)
    if not addresses:
        await safe_chat(context, chat_id, "You don't have any addresses set.")
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton(addr, callback_data=addr)] for addr in addresses]
    keyboard.append([InlineKeyboardButton("Exit", callback_data='exit')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await safe_chat(context, chat_id, "Select address to be released:", reply_markup)
    return RELEASE_CHOOSE_ADDRESS

async def handle_release_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
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
    return RELEASE_CONFIRM

async def handle_release_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'yes_delete':
        address = context.user_data['address_to_delete']
        release_address_from_database(sql_connection, address)
        await safe_chat(context, update.effective_chat.id, f"Address {address} released successfully.")
    else:
        await safe_chat(context, update.effective_chat.id, "Operation cancelled.")
    return ConversationHandler.END

def get_release_address_conv_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("vapauta", release_address, filters.ChatType.GROUPS | filters.ChatType.PRIVATE)],
        states={
            RELEASE_CHOOSE_ADDRESS: [CallbackQueryHandler(handle_release_selection)],
            RELEASE_CONFIRM: [CallbackQueryHandler(handle_release_confirm)]
        },
        fallbacks=[],
        conversation_timeout=300,  # 5 minutes
        per_user=True,
        per_chat=True
    )