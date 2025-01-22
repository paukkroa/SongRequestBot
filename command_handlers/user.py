from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, filters

from errors.query_errors import AddressExpiredError, AddressNotActiveError, AddressNotFoundError
from utils.chatting import safe_chat
from utils.logger import get_logger
from utils.config import sql_connection
from db.user_queries import get_recipient, get_nickname, add_user
from processes import SongRequest

logger = get_logger(__name__)

async def set_recipient(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set the recipient for messages"""

    chat_id = update.effective_chat.id
    await safe_chat(context, chat_id, "Please provide the recipient code:")
    context.application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, _get_code
    ))

async def _get_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    address = update.message.text

    # Check if the address is valid

async def register_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Register a new user"""
    user_id = update.effective_user.id

    # Ask if user wants a nickname
    keyboard = [[InlineKeyboardButton("Yes", callback_data='yes_nickname'),
                 InlineKeyboardButton("No", callback_data='no_nickname')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Would you like to set a nickname?', reply_markup=reply_markup)

    # Wait for callback
    callback_query = await context.application.update_queue.get()
    await callback_query.answer()

    if callback_query.data == 'yes_nickname':
        await update.message.reply_text('Please enter your nickname:')
        msg = await context.application.update_queue.get()
        nickname = msg.text
    else:
        nickname = f"Unknown user"

    # Add user
    add_user(user_id, nickname=nickname, role='user')

async def song_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle private messages which should be song requests"""

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
        await safe_chat(context, user_id, "No such code found.")
        return
    
    nickname = get_nickname(user_id)
    
    # Get song request info
    song_request = SongRequest(update, context, recipient, nickname)
    await song_request.process_request()
    
    
    