import sqlite3
from utils.logger import get_logger
from datetime import datetime, timedelta, timezone

logger = get_logger(__name__)

def get_release_ready_addresses(conn: sqlite3.Connection):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT address, chat_id 
        FROM R_CHAT_ADDRESS 
        WHERE valid_until < datetime('now', 'utc', '-10 days')
    """)
    results = cursor.fetchall()
    cursor.close()
    return {addr: chat_id for addr, chat_id in results}

def get_just_expired_addresses(conn: sqlite3.Connection):
    """Get addresses that have expired in the last hour"""
    cursor = conn.cursor()
    now = datetime.now(timezone.utc)
    one_hour_ago = now - timedelta(hours=1)
    cursor.execute("""
        SELECT address, chat_id 
        FROM R_CHAT_ADDRESS 
        WHERE valid_until > ? 
        AND valid_until <= ?
    """, (one_hour_ago, now))
    results = cursor.fetchall()
    cursor.close()
    return {addr: chat_id for addr, chat_id in results}