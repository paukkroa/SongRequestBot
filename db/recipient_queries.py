import sqlite3
from datetime import timezone, datetime

from utils.logger import get_logger
from errors.query_errors import AddressNotFoundError, AddressExpiredError

logger = get_logger(__name__)

def add_new_recipient(conn: sqlite3.Connection, chat_id: str, chat_type: str):
    cursor = conn.cursor()
    # Check if record already exists
    cursor.execute('''
        SELECT 1 FROM D_RECIPIENT_CHAT 
        WHERE chat_id = ?
    ''', (chat_id,))
    
    if cursor.fetchone() is None:
        cursor.execute('''
            INSERT INTO D_RECIPIENT_CHAT (chat_id, chat_type)
            VALUES (?, ?)
        ''', (chat_id, chat_type))
        conn.commit()
        logger.info(f"New recipient created {chat_id}")
        cursor.close()
        return True
    else:
        logger.error("Recipient already exists")
        cursor.close()
        return False
    

def get_recipient_chat_id(conn: sqlite3.Connection, chat_id: str):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT chat_id 
        FROM D_RECIPIENT_CHAT 
        WHERE chat_id = ?
    ''', (chat_id,))
    chat_id = cursor.fetchone()
    cursor.close()
    return chat_id is not None

def get_address_attributes(conn: sqlite3.Connection, address: str):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT address, chat_id, password, active, valid_until 
        FROM R_CHAT_ADDRESS 
        WHERE address = ?
    ''', (address,))
    result = cursor.fetchone()
    cursor.close()
    
    if result:
        return {
            'address': result[0],
            'chat_id': result[1],
            'password': result[2],
            'active': result[3],
            'valid_until': result[4]
        }
    return None

def get_amount_of_recipient_addresses(conn: sqlite3.Connection, chat_id: str):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) 
        FROM R_CHAT_ADDRESS 
        WHERE chat_id = ?
    ''', (chat_id,))
    amount = cursor.fetchone()
    cursor.close()
    return amount[0]

def create_new_address(conn: sqlite3.Connection, address: str, chat_id: str, password: str = None, valid_until: datetime = None):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO R_CHAT_ADDRESS (address, chat_id, password, valid_until)
        VALUES (?, ?, ?, ?)
    ''', (address, chat_id, password, valid_until))
    conn.commit()
    cursor.close()

def expire_address(conn: sqlite3.Connection, address: str):
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE R_CHAT_ADDRESS 
        SET valid_until = datetime('now'),
            uby = 'system',
            udate = datetime('now')
        WHERE address = ?
    ''', (address,))
    conn.commit()
    cursor.close()

    logger.info(f"Address {address} expired")


def get_recipient_addresses(conn: sqlite3.Connection, chat_id: str):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT address, active, valid_until
        FROM R_CHAT_ADDRESS 
        WHERE chat_id = ?
        AND (valid_until >= datetime('now', '-30 days') OR valid_until IS NULL)
    ''', (chat_id,))
    addresses = cursor.fetchall()
    cursor.close()

    if not addresses:
        return None

    now = datetime.now(timezone.utc)
    active_addresses = []
    inactive_addresses = []

    for addr in addresses:
        address, is_active, valid_until = addr
        infinity = False
        try:
            try:
                parsed_date = datetime.strptime(valid_until, '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                parsed_date = datetime.strptime(valid_until, '%Y-%m-%d %H:%M:%S')
            valid_date = valid_until is None or parsed_date.replace(tzinfo=timezone.utc) > now
        except TypeError: # valid_until is None --> infinite validity
            valid_date = True
            infinity = True
        
        if is_active and valid_date:
            if not infinity:
                utc_time = parsed_date.replace(tzinfo=timezone.utc) if valid_until else None
                local_time = utc_time.astimezone() if utc_time else None
                display_date = f" (expires at {local_time.strftime('%d.%m.%Y %H.%M')})" if local_time else ""
                active_addresses.append(f"{address}{display_date}")
            else:
                active_addresses.append(f"{address} (always valid)")
        else:
            if not valid_date:
                status = "expired"
            elif not is_active:
                status = "inactive"
            inactive_addresses.append(f"{address} ({status})")

    result = "Active addresses:\n" + "\n".join(active_addresses) if active_addresses else "No active addresses"
    result += "\n\nInactive addresses:\n" + "\n".join(inactive_addresses) if inactive_addresses else "\n\nNo inactive addresses"
    
    return result

def list_recipient_addresses(conn: sqlite3.Connection, chat_id: str):
    # Returns a list of all addresses for the recipient in R_CHAT_ADDRESS
    cursor = conn.cursor()
    cursor.execute('''
        SELECT address
        FROM R_CHAT_ADDRESS 
        WHERE chat_id = ?
    ''', (chat_id,))
    addresses = cursor.fetchall()
    cursor.close()

    if not addresses:
        return None
    
    return [addr[0] for addr in addresses]

def list_valid_recipient_addresses(conn: sqlite3.Connection, chat_id: str):
    # Returns a list of all addresses for the recipient in R_CHAT_ADDRESS where valid_until is in future
    cursor = conn.cursor()
    cursor.execute('''
        SELECT address
        FROM R_CHAT_ADDRESS 
        WHERE chat_id = ?
        AND (valid_until > datetime('now') OR valid_until IS NULL)
    ''', (chat_id,))
    addresses = cursor.fetchall()
    cursor.close()

    if not addresses:
        return None
    
    return [addr[0] for addr in addresses]

def toggle_active(conn: sqlite3.Connection, address: str):
    cursor = conn.cursor()
    # First check if address exists and get active status and valid_until
    cursor.execute('''
        SELECT active, valid_until
        FROM R_CHAT_ADDRESS 
        WHERE address = ?
    ''', (address,))
    result = cursor.fetchone()
    cursor.close()

    if not result:
        raise AddressNotFoundError("Address not found")

    active, valid_until = result
    
    # Check if address has expired
    if valid_until:
        try:
            parsed_date = datetime.strptime(valid_until, '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            parsed_date = datetime.strptime(valid_until, '%Y-%m-%d %H:%M:%S')
        if parsed_date.replace(tzinfo=timezone.utc) <= datetime.now(timezone.utc):
            raise AddressExpiredError("Address has expired")

    # Toggle active status and update uby/udate
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE R_CHAT_ADDRESS
        SET active = ?,
            uby = 'system',
            udate = datetime('now')
        WHERE address = ?
    ''', (1 if active == 0 else 0, address))
    conn.commit() 
    cursor.close()
    
    logger.info(f"Address {address} active status toggled to {1 if active == 0 else 0}")

    return True

def release_address_from_database(conn: sqlite3.Connection, address: str):
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM R_CHAT_ADDRESS 
        WHERE address = ?
    ''', (address,))
    conn.commit()
    cursor.close()

    logger.info(f"Address {address} released")


def get_expired_addresses(conn: sqlite3.Connection, chat_id: str):
    """Get expired addresses for the current recipient"""
    cursor = conn.cursor()
    cursor.execute('''
        SELECT address
        FROM R_CHAT_ADDRESS 
        WHERE chat_id = ?
        AND valid_until < datetime('now')
    ''', (chat_id,))
    addresses = cursor.fetchall()
    cursor.close()

    if not addresses:
        return None

    return [addr[0] for addr in addresses]

def renew_address(conn: sqlite3.Connection, address: str, valid_until: datetime):
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE R_CHAT_ADDRESS 
        SET valid_until = ?,
            uby = 'renewal_process',
            udate = datetime('now')
        WHERE address = ?
    ''', (valid_until, address))
    conn.commit()
    cursor.close()

    logger.info(f"Address {address} renewed until {valid_until}")
    return True