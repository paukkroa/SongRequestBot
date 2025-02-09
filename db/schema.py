import sqlite3
from utils.logger import get_logger

logger = get_logger(__name__)

def connect(db: str = '/app/database/songrequestbot.db') -> sqlite3.Connection:
    conn = sqlite3.connect(db)
    logger.info(f'Connected to database at {db}')
    return conn

def close_connection(conn: sqlite3.Connection) -> None:
    logger.info('Closing database connection')
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
        iby TEXT DEFAULT 'system',
        uby TEXT DEFAULT 'system',
        idate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        udate TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    ''')

    # Addresses and the chat they are linked to D_ADDRESS
    conn.execute('''
    CREATE TABLE IF NOT EXISTS R_CHAT_ADDRESS (
        address TEXT PRIMARY KEY,
        chat_id TEXT NOT NULL,
        password TEXT,
        active INTEGER DEFAULT 1,
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

    logger.info('Tables created if they did not exist yet.')