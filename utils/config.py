import os
from db import schema as db
from utils.logger import get_logger

logger = get_logger(__name__)

BOT_TOKEN = os.environ['BOT_TOKEN']
try:
    LANGUAGE = os.environ['BOT_LANGUAGE']
except:
    LANGUAGE = 'en'
    logger.warning('No language specified, defaulting to English')

sql_connection = db.connect()