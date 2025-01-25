from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, filters, ConversationHandler, CallbackQueryHandler, CommandHandler
import hashlib

from errors.query_errors import AddressExpiredError, AddressNotActiveError, AddressNotFoundError
from utils.chatting import safe_chat
from utils.logger import get_logger
from utils.config import sql_connection
from db import *

from warnings import filterwarnings
from telegram.warnings import PTBUserWarning

filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)

logger = get_logger(__name__)

# States for recipient setting conversation
CODE_INPUT, PASSWORD_INPUT, CHANGE_CODE = 0, 1, 2

async def set_recipient(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point for setting recipient conversation"""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Check if the chat is a private chat
    if update.effective_chat.type != 'private':
        await safe_chat(context, chat_id, "This command can only be used in private chats.")
        return ConversationHandler.END
    
    # Check if user exists
    if not user_exists(sql_connection, user_id):
        await safe_chat(context, user_id, "You need to register before using the bot!")
        return ConversationHandler.END

    current_address = get_current_address(sql_connection, user_id)
    if current_address:
        await safe_chat(context, chat_id, f"Your current code is: {current_address}")
        keyboard = [
            [
                InlineKeyboardButton("Change code", callback_data="change"),
                InlineKeyboardButton("Exit", callback_data="exit")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_chat(context, chat_id, "Would you like to change the code?", reply_markup=reply_markup)
        return CHANGE_CODE
    
    await safe_chat(context, chat_id, "Please provide the code:")
    return CODE_INPUT

async def handle_change_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle whether to change the existing code"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "exit":
        await safe_chat(context, update.effective_chat.id, "Operation cancelled.")
        return ConversationHandler.END
    
    await safe_chat(context, update.effective_chat.id, "Please provide the new code:")
    return CODE_INPUT

async def handle_code_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the code input"""
    context.user_data['address'] = update.message.text
    
    if is_password_set(sql_connection, context.user_data['address']):
        context.user_data['password_attempts'] = 0
        await safe_chat(context, update.effective_chat.id, "Please enter the password:")
        return PASSWORD_INPUT
    
    try:
        result = set_user_forward_address(sql_connection, update.effective_user.id, context.user_data['address'])
        await safe_chat(context, update.effective_chat.id, "Code accepted! You can now start sending song requests using the /biisitoive command.")
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error setting recipient: {e}")
        await safe_chat(context, update.effective_chat.id, str(e))
        return ConversationHandler.END

async def handle_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle password verification"""
    password = update.message.text
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    if check_password_match(sql_connection, context.user_data['address'], hashed_password):
        try:
            result = set_user_forward_address(sql_connection, update.effective_user.id, context.user_data['address'])
            await safe_chat(context, update.effective_chat.id, "Code accepted! You can now start sending song requests using the /biisitoive command.")
            return ConversationHandler.END
        except Exception as e:
            logger.error(f"Error setting recipient: {e}")
            await safe_chat(context, update.effective_chat.id, str(e))
            return ConversationHandler.END
    
    context.user_data['password_attempts'] = context.user_data.get('password_attempts', 0) + 1
    if context.user_data['password_attempts'] >= 3:
        await safe_chat(context, update.effective_chat.id, "Maximum password attempts reached.")
        return ConversationHandler.END
    
    await safe_chat(context, update.effective_chat.id, "Incorrect password. Please try again.")
    return PASSWORD_INPUT

async def timeout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle conversation timeout"""
    await safe_chat(context, update.effective_chat.id, "Operation timed out. Please try again.")
    return ConversationHandler.END

def get_set_recipient_conv_handler():
    """Get the conversation handler for setting recipient"""
    return ConversationHandler(
        entry_points=[MessageHandler(filters.COMMAND & filters.Regex('^/koodi$'), set_recipient)],
        states={
            CHANGE_CODE: [CallbackQueryHandler(handle_change_code)],
            CODE_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_code_input)],
            PASSWORD_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_password)]
        },
        fallbacks=[MessageHandler(filters.ALL, timeout), CommandHandler("cancel", lambda u,c: ConversationHandler.END)],
        conversation_timeout=300,  # 5 minutes timeout
        per_user=True,
        per_chat=True
    )


# States for nickname change conversation
NICKNAME_CHANGE, NEW_NICKNAME = 5, 6

async def change_nickname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point for changing nickname conversation"""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if update.effective_chat.type != 'private':
        await safe_chat(context, chat_id, "This command can only be used in private chats.")
        return ConversationHandler.END
    
    if not user_exists(sql_connection, user_id):
        await safe_chat(context, user_id, "You need to register before using the bot!")
        return ConversationHandler.END

    current_nickname = get_nickname(sql_connection, user_id)
    if current_nickname:
        await safe_chat(context, chat_id, f"Your current nickname is: {current_nickname}")
        keyboard = [
            [
                InlineKeyboardButton("Change nickname", callback_data="change"),
                InlineKeyboardButton("Exit", callback_data="exit")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_chat(context, chat_id, "Would you like to change your nickname?", reply_markup=reply_markup)
        return NICKNAME_CHANGE
    
    await safe_chat(context, chat_id, "Please enter your new nickname:")
    return NEW_NICKNAME

async def handle_nickname_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle whether to change the existing nickname"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "exit":
        await safe_chat(context, update.effective_chat.id, "Operation cancelled.")
        return ConversationHandler.END
    
    await safe_chat(context, update.effective_chat.id, "Please enter your new nickname:")
    return NEW_NICKNAME

async def handle_new_nickname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the new nickname input"""
    new_nickname = update.message.text
    update_nickname(sql_connection, update.effective_user.id, new_nickname)
    await safe_chat(context, update.effective_chat.id, f"Your nickname has been updated to: {new_nickname}")
    return ConversationHandler.END

def get_change_nickname_conv_handler():
    """Get the conversation handler for changing nickname"""
    return ConversationHandler(
        entry_points=[MessageHandler(filters.COMMAND & filters.Regex('^/nikki$'), change_nickname)],
        states={
            NICKNAME_CHANGE: [CallbackQueryHandler(handle_nickname_change)],
            NEW_NICKNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_nickname)]
        },
        fallbacks=[MessageHandler(filters.ALL, timeout), CommandHandler("cancel", lambda u,c: ConversationHandler.END)],
        conversation_timeout=300,
        per_user=True,
        per_chat=True
    )


# States for the conversation
NICKNAME_CHOICE, ENTER_NICKNAME = 10, 11

async def register_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if update.effective_chat.type != 'private':
        await safe_chat(context, chat_id, "This command can only be used in private chats.")
        return ConversationHandler.END

    if user_exists(sql_connection, user_id):
        await safe_chat(context, user_id, "You are already registered!")
        return ConversationHandler.END

    keyboard = [
        [
            InlineKeyboardButton("Yes", callback_data="yes"),
            InlineKeyboardButton("No", callback_data="no")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await safe_chat(context, chat_id, 'Hello there! Would you like to set a nickname?', reply_markup=reply_markup)
    return NICKNAME_CHOICE

async def nickname_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'yes':
        await safe_chat(context, query.message.chat_id, 'Please enter your nickname:')
        return ENTER_NICKNAME
    else:
        add_user(sql_connection, update.effective_user.id, nickname=None, role='user')
        await safe_chat(context, query.message.chat_id, "Welcome mysterious user!")
        return ConversationHandler.END

async def save_nickname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nickname = update.message.text
    user_id = update.effective_user.id
    add_user(sql_connection, user_id, nickname=nickname, role='user')
    await safe_chat(context, update.effective_chat.id, f"Welcome {nickname}!")
    return ConversationHandler.END

async def timeout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_chat(context, update.effective_chat.id, "Registering failed, please send /start again.")
    return ConversationHandler.END

def get_register_conv_handler():
    return ConversationHandler(
        entry_points=[MessageHandler(filters.COMMAND & filters.Regex('^/start$'), register_user)],
        states={
            NICKNAME_CHOICE: [CallbackQueryHandler(nickname_choice)],
            ENTER_NICKNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_nickname)]
        },
        fallbacks=[MessageHandler(filters.ALL, timeout), CommandHandler("cancel", lambda u,c: ConversationHandler.END)],
        conversation_timeout=300,
        per_user=True,
        per_chat=True
    )

SONG_NAME, ARTIST_NAME, NOTES, CONFIRMATION = 20, 21, 22, 23

async def song_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point for song request conversation"""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Check if the chat is a private chat
    if update.effective_chat.type != 'private':
        await safe_chat(context, chat_id, "This command can only be used in private chats.")
        return ConversationHandler.END

    # Check if user exists
    if not user_exists(sql_connection, user_id):
        await safe_chat(context, user_id, "You need to register before using the bot!")
        return ConversationHandler.END

    # Check if the user has a forwarding address
    try:
        recipient = get_recipient(sql_connection, user_id)
        context.user_data['recipient'] = recipient
        context.user_data['nickname'] = get_nickname(sql_connection, user_id)
    except (AddressExpiredError, AddressNotActiveError, AddressNotFoundError) as e:
        error_messages = {
            AddressExpiredError: "Code has expired.",
            AddressNotActiveError: "Code has been turned off by the recipient.",
            AddressNotFoundError: "You have not set a code yet. Set a code with /koodi"
        }
        await safe_chat(context, user_id, error_messages[type(e)])
        return ConversationHandler.END

    await safe_chat(context, chat_id, "What's the name of the song?")
    return SONG_NAME

async def song_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle song name input"""
    context.user_data['song_name'] = update.message.text
    await safe_chat(context, update.effective_chat.id, "Who's the artist?")
    return ARTIST_NAME

async def artist_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle artist name input"""
    context.user_data['artist_name'] = update.message.text
    keyboard = [[InlineKeyboardButton("Skip notes", callback_data='skip_notes')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await safe_chat(context, update.effective_chat.id, 
                   "Add any notes about your request (max 150 characters) or click Skip:", 
                   reply_markup=reply_markup)
    return NOTES

async def notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle notes input"""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        if query.data == 'skip_notes':
            context.user_data['notes'] = ""
            return await show_confirmation(update, context)

    if len(update.message.text) > 150:
        await safe_chat(context, update.effective_chat.id, 
                       "Notes too long! Please keep it under 150 characters. Try again:")
        return NOTES

    context.user_data['notes'] = update.message.text
    return await show_confirmation(update, context)

async def show_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show confirmation message"""
    keyboard = [[InlineKeyboardButton("Yes", callback_data='yes'),
                InlineKeyboardButton("No", callback_data='no')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    confirm_text = (f"Confirm song request:\n"
                   f"Song: {context.user_data['song_name']}\n"
                   f"Artist: {context.user_data['artist_name']}")
    if context.user_data['notes']:
        confirm_text += f"\nNotes: {context.user_data['notes']}"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(confirm_text, reply_markup=reply_markup)
    else:
        await safe_chat(context, update.effective_chat.id, confirm_text, reply_markup=reply_markup)
    return CONFIRMATION

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle confirmation"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'yes':
        message = (f"New song request from {context.user_data['nickname']}!\n"
                  f"Song: {context.user_data['song_name']}\n"
                  f"Artist: {context.user_data['artist_name']}\n"
                  f"Notes: {context.user_data['notes']}")
        await safe_chat(context, context.user_data['recipient'], message)
        await safe_chat(context, update.effective_chat.id, "Song request sent!")
        logger.info(f"Song request from {update.effective_user.id} sent to {context.user_data['recipient']}")
    else:
        await safe_chat(context, update.effective_chat.id, "Song request cancelled.")
        logger.info(f"Song request from {update.effective_user.id} cancelled")
    
    return ConversationHandler.END

async def timeout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle conversation timeout"""
    await safe_chat(context, update.effective_chat.id, "Song request timed out. Please try again.")
    return ConversationHandler.END

def get_song_request_conv_handler():
    """Get the conversation handler for song requests"""
    return ConversationHandler(
        entry_points=[MessageHandler(filters.COMMAND & filters.Regex('^/biisitoive$'), song_request)],
        states={
            SONG_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, song_name)],
            ARTIST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, artist_name)],
            NOTES: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, notes),
                CallbackQueryHandler(notes, pattern='^skip_notes$')
            ],
            CONFIRMATION: [CallbackQueryHandler(confirm, pattern='^(yes|no)$')]
        },
        fallbacks=[MessageHandler(filters.ALL, timeout), CommandHandler("cancel", lambda u,c: ConversationHandler.END)],
        conversation_timeout=300,
        per_user=True,
        per_chat=True 
    )
    
