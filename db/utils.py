import sqlite3

def get_release_ready_addresses(conn: sqlite3.Connection):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT address, chat_id 
        FROM R_CHAT_ADDRESS 
        WHERE valid_until < datetime('now', '-10 days')
    """)
    results = cursor.fetchall()
    cursor.close()
    return {addr: chat_id for addr, chat_id in results}