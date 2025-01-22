import sqlite3
from datetime import datetime

from utils.config import sql_connection
from errors.query_errors import *
from utils.logger import get_logger

logger = get_logger(__name__)

def get_forward_address(sql_connection, user_id: str):
    cursor = sql_connection.cursor()
    cursor.execute('''
        SELECT address
        FROM R_FORWARD_ADDRESS
        WHERE user_id = ?
    ''', (user_id,))
    address = cursor.fetchone()
    cursor.close()
    return address

def get_address_chat_id(sql_connection, address: str):
    cursor = sql_connection.cursor()
    cursor.execute('''
        SELECT chat_id
        FROM R_CHAT_ADDRESS
        WHERE address = ?
    ''', (address,))
    chat_id = cursor.fetchone()
    cursor.close()
    return chat_id

def is_recipient_active(sql_connection, user_id: str):
    address = get_forward_address(sql_connection, user_id)
    if address is None:
        return False
    
    cursor = sql_connection.cursor()
    cursor.execute('''
        SELECT active
        FROM R_CHAT_ADDRESS
        WHERE address = ?
    ''', (address[0],))
    active = cursor.fetchone()
    cursor.close()
    
    if active is None:
        return False
    return active[0] == 1

def is_recipient_valid(sql_connection, user_id: str):
    address = get_forward_address(sql_connection, user_id)
    if address is None:
        return False
    
    cursor = sql_connection.cursor()
    cursor.execute('''
        SELECT valid_until
        FROM R_CHAT_ADDRESS
        WHERE address = ?
    ''', (address[0],))
    valid_until = cursor.fetchone()
    cursor.close()
    
    if valid_until is None:
        return False
    return valid_until[0] > datetime.now()

def get_recipient(sql_connection, user_id: str):
    address = get_forward_address(sql_connection, user_id)
    if address is None:
        raise AddressNotFoundError("Forward address not found for user")
    
    if not is_recipient_active(sql_connection, user_id):
        raise AddressNotActiveError("Forward address is not active")
    
    if not is_recipient_valid(sql_connection, user_id):
        raise AddressExpiredError("Forward address has expired")
    
    chat_id = get_address_chat_id(sql_connection, address[0])
    return chat_id[0]

def add_user(user_id: str, nickname: str, role: str):
    cursor = sql_connection.cursor()
    
    # Check if user already exists
    cursor.execute('''
        SELECT user_id 
        FROM D_USER 
        WHERE user_id = ?
    ''', (user_id,))
    
    if cursor.fetchone() is not None:
        cursor.close()
        logger.error("User exists in chat")
        return

    cursor.execute('''
        INSERT INTO D_USER (user_id, nickname, role)
        VALUES (?, ?, ?)
    ''', (user_id, nickname, role))
    sql_connection.commit()
    cursor.close()

def get_nickname(user_id: str):
    cursor = sql_connection.cursor()
    cursor.execute('''
        SELECT nickname
        FROM D_USER
        WHERE user_id = ?
    ''', (user_id,))
    nickname = cursor.fetchone()
    cursor.close()
    
    if nickname is None:
        return None
    return nickname[0]