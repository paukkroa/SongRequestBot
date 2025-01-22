import sqlite3

def connect(db: str = 'songrequestbot.db') -> sqlite3.Connection:
    conn = sqlite3.connect(db)
    return conn

def close_connection(conn: sqlite3.Connection) -> None:
    conn.close()

def create_tables(conn: sqlite3.Connection) -> None:
    # Users who send the requests and the recipients
    conn.execute('''
    CREATE TABLE IF NOT EXISTS D_USER (
        user_id TEXT PRIMARY KEY,
        nickname TEXT,
        role TEXT NOT NULL,
        iby TEXT DEFAULT 'system',
        uby TEXT DEFAULT 'system',
        idate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        udate TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    ''')

    # Users who send the requests and the recipients
    conn.execute('''
    CREATE TABLE IF NOT EXISTS D_RECIPIENT_CHAT (
        chat_id TEXT PRIMARY KEY,
        chat_type TEXT NOT NULL,
        role TEXT NOT NULL,
        iby TEXT DEFAULT 'system',
        uby TEXT DEFAULT 'system',
        idate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        udate TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    ''')

    # Addresses and the chat they are linked to D_ADDRESS
    conn.execute('''
    CREATE TABLE IF NOT EXISTS R_CHAT_ADDRESS (
        address INTEGER PRIMARY KEY,
        chat_id TEXT NOT NULL,
        password TEXT,
        active INTEGER DEFAULT '1',
        valid_until TIMESTAMP,
        iby TEXT DEFAULT 'system',
        uby TEXT DEFAULT 'system',
        idate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        udate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (chat_id) REFERENCES D_RECIPIENT_CHAT(chat_id)
    );
    ''')

    # Forwarding addresses R_FORWARD_ADDRESS
    conn.execute('''
    CREATE TABLE IF NOT EXISTS R_FORWARD_ADDRESS (
        user_id TEXT NOT NULL,
        address TEXT NOT NULL,
        iby TEXT DEFAULT 'system',
        uby TEXT DEFAULT 'system',
        idate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        udate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES D_USER(user_id),
        FOREIGN KEY (address) REFERENCES D_ADDRESS(address)
    );
    ''')