from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, filters

from errors.query_errors import AddressExpiredError, AddressNotActiveError, AddressNotFoundError
from utils.chatting import safe_chat
from utils.logger import get_logger
from utils.config import sql_connection
from db import get_recipient, get_nickname, add_user, user_exists
from processes import SongRequest, SetRecipient

logger = get_logger(__name__)

async def set_recipient(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set the recipient for messages"""

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Check if the chat is a private chat
    if update.effective_chat.type != 'private':
        await safe_chat(context, chat_id, "This command can only be used in private chats.")
        return
    
    # Check if user exists
    if not user_exists(sql_connection, user_id):
        await safe_chat(context, user_id, "You need to register before using the bot!")
        return

    set_recipient = SetRecipient(update, context, user_id, chat_id, sql_connection)
    await set_recipient.process_request()


async def register_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Register a new user"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Check if the chat is a private chat
    if update.effective_chat.type != 'private':
        await safe_chat(context, chat_id, "This command can only be used in private chats.")
        return
    

    # Check if user already exists
    if user_exists(sql_connection, user_id):
        await safe_chat(context, user_id, "You are already registered!")
        return

    # Ask if user wants a nickname
    keyboard = [[InlineKeyboardButton("Yes", callback_data='yes_nickname'),
                 InlineKeyboardButton("No", callback_data='no_nickname')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Hello there! Would you like to set a nickname?', reply_markup=reply_markup)

    # Wait for callback
    callback_query = await context.application.update_queue.get()
    await context.bot.answer_callback_query(callback_query.callback_query.id)

    if callback_query.callback_query.data == 'yes_nickname':
        await update.message.reply_text('Please enter your nickname:')
        msg = await context.application.update_queue.get()
        nickname = msg.message.text
    else:
        nickname = f"Unknown user"

    # Add user
    add_user(sql_connection, user_id, nickname=nickname, role='user')
    if nickname != "Unknown user":
        await safe_chat(context, user_id, f"Welcome {nickname}!")
    else:
        await safe_chat(context, user_id, "Welcome mysterious user!")

async def song_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle private messages which should be song requests"""

    chat_id = update.effective_chat.id

    # Check if the chat is a private chat
    if update.effective_chat.type != 'private':
        await safe_chat(context, chat_id, "This command can only be used in private chats.")
        return

    # TODO: check when the user last sent a song request, limit to once per 10 minutes

    user_id = update.effective_user.id
    logger.info(f"Initiated song request from {user_id}")

    # Check if the user has a forwarding address
    try:
        recipient = get_recipient(sql_connection, user_id)
    except AddressExpiredError as e:
        await safe_chat(context, user_id, "Code has expired.")
        return
    except AddressNotActiveError as e:
        await safe_chat(context, user_id, "Code is not active.")
        return
    except AddressNotFoundError as e:
        await safe_chat(context, user_id, "You have not set a code yet. Set a code with /koodi")
        return
    
    nickname = get_nickname(sql_connection, user_id)
    
    # Get song request info
    song_request = SongRequest(update, context, recipient, nickname, sql_connection)
    await song_request.process_request()
    
    
    