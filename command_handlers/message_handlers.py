from telegram import Update
from telegram.ext import ContextTypes, MessageHandler

from db.user_queries import get_recipient
from errors.query_errors import AddressExpiredError, AddressNotActiveError, AddressNotFoundError

from utils.chatting import safe_chat
from utils.config import sql_connection

async def handle_private_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle private messages which should be song requests"""
    user_id = update.effective_user.id
    song_request = update.message.text

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
    
    # Send the song request to the recipient
    # await safe_chat(context, recipient, song_request)