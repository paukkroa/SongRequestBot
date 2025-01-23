import sqlite3
from datetime import datetime, timezone

from errors.query_errors import *
from utils.logger import get_logger

logger = get_logger(__name__)

def get_forward_address(conn: sqlite3.Connection, user_id: str):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT address
        FROM R_FORWARD_ADDRESS
        WHERE user_id = ?
    ''', (user_id,))
    address = cursor.fetchone()
    cursor.close()
    return address

def get_address_chat_id(conn: sqlite3.Connection, address: str):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT chat_id
        FROM R_CHAT_ADDRESS
        WHERE address = ?
    ''', (address,))
    chat_id = cursor.fetchone()
    cursor.close()
    return chat_id

def is_recipient_active(conn: sqlite3.Connection, user_id: str):
    address = get_forward_address(conn, user_id)
    if address is None:
        return False
    
    cursor = conn.cursor()
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

def is_recipient_valid(conn: sqlite3.Connection, user_id: str):
    address = get_forward_address(conn, user_id)
    if address is None:
        return False
    
    cursor = conn.cursor()
    cursor.execute('''
        SELECT valid_until
        FROM R_CHAT_ADDRESS
        WHERE address = ?
    ''', (address[0],))
    valid_until = cursor.fetchone()
    cursor.close()
    
    if valid_until is None:
        return True
    valid_until_datetime = datetime.fromisoformat(valid_until[0]).replace(tzinfo=timezone.utc)
    return valid_until_datetime > datetime.now(timezone.utc)

def get_recipient(conn: sqlite3.Connection, user_id: str):
    address = get_forward_address(conn, user_id)
    if address is None:
        raise AddressNotFoundError("Forward address not found for user")
    
    if not is_recipient_active(conn, user_id):
        raise AddressNotActiveError("Forward address is not active")
    
    if not is_recipient_valid(conn, user_id):
        raise AddressExpiredError("Forward address has expired")
    
    chat_id = get_address_chat_id(conn, address[0])
    return chat_id[0]

def add_user(conn: sqlite3.Connection, user_id: str, nickname: str, role: str):
    cursor = conn.cursor()
    
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
    conn.commit()
    cursor.close()
    logger.info(f"New user {user_id} with nickname {nickname}")

def get_nickname(conn: sqlite3.Connection, user_id: str):
    cursor = conn.cursor()
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

def address_exists(conn: sqlite3.Connection, address: str):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT address
        FROM R_CHAT_ADDRESS
        WHERE address = ?
    ''', (address,))
    result = cursor.fetchone()
    cursor.close()
    
    return result is not None

def user_exists(conn: sqlite3.Connection, user_id: str):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id
        FROM D_USER
        WHERE user_id = ?
    ''', (user_id,))
    result = cursor.fetchone()
    cursor.close()
    
    return result is not None

def set_user_forward_address(conn: sqlite3.Connection, user_id: str, address: str):
    cursor = conn.cursor()

    # check if the user exists in D_USER
    exists = user_exists(conn, user_id)
    if not exists:
        raise UserNotFoundError("User not found")

    # Check if the address exists in R_CHAT_ADDRESS 
    result = address_exists(conn, address)
    if not result:
        raise AddressNotFoundError("Address not found")
    
    # Check if the user already has a forward address
    result = get_forward_address(conn, user_id)
    if result is not None:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            UPDATE R_FORWARD_ADDRESS
            SET address = ?,
            UBY = 'system',
            UDATE = ?
            WHERE user_id = ?
        ''', (address, current_time, user_id))
    else:
        cursor.execute('''
            INSERT INTO R_FORWARD_ADDRESS (user_id, address)
            VALUES (?, ?)
        ''', (user_id, address))

    conn.commit()
    cursor.close()
    return True

def check_password_match(conn: sqlite3.Connection, address: str, password: str):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT password
        FROM R_CHAT_ADDRESS
        WHERE address = ?
    ''', (address,))
    result = cursor.fetchone()
    cursor.close()
    
    if result is None:
        return False
    return result[0] == password

def is_password_set(conn: sqlite3.Connection, address: str):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT password
        FROM R_CHAT_ADDRESS
        WHERE address = ?
    ''', (address,))
    result = cursor.fetchone()
    cursor.close()

    result = result[0] if result is not None else None

    if result == "":
        return False
    
    return result is not None

def get_current_address(conn: sqlite3.Connection, user_id: str):
    address = get_forward_address(conn, user_id)
    if address is None:
        return None
    return address[0]