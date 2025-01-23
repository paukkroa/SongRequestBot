import sqlite3

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
    
    cursor.close()

def get_recipient_chat_id(conn: sqlite3.Connection, chat_id: str):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT chat_id 
        FROM D_RECIPIENT_CHAT 
        WHERE chat_id = ?
    ''', (chat_id,))
    chat_id = cursor.fetchone()
    cursor.close()
    return chat_id

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

def create_new_address(conn: sqlite3.Connection, address: str, chat_id: str, password: str = None, valid_until: str = None):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO R_CHAT_ADDRESS (address, chat_id, password, valid_until)
        VALUES (?, ?, ?, ?)
    ''', (address, chat_id, password, valid_until))
    conn.commit()
    cursor.close()

def remove_address(conn: sqlite3.Connection, address: str):
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM R_CHAT_ADDRESS 
        WHERE address = ?
    ''', (address,))
    conn.commit()
    cursor.close()

def get_recipient_addresses(conn: sqlite3.Connection, chat_id: str):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT address, password, active, valid_until 
        FROM R_CHAT_ADDRESS 
        WHERE chat_id = ?
    ''', (chat_id,))
    addresses = cursor.fetchall()
    cursor.close()
    return addresses