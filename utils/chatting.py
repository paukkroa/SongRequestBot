from telegram.error import BadRequest, RetryAfter, Forbidden
import asyncio
from telegram.ext import ContextTypes
from utils.logger import get_logger

logger = get_logger(__name__)

async def safe_chat(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message: str, reply_markup=None):
    try:
        await context.bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)
    except RetryAfter as e:
        logger.info(f"Caught flood control, retrying after {e.retry_after+1} seconds")
        await asyncio.sleep(e.retry_after+1)
        await safe_chat(context, chat_id, message, reply_markup)
    except Forbidden as e: # Player has not initiated a private chat with the bot
        logger.info(e)
        return e
    except BadRequest as e:
        logger.info(e)
        return e