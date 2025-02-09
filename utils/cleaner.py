from db import *
from utils.chatting import safe_chat
from utils.logger import get_logger

logger = get_logger(__name__)

async def clean_expired_addresses(context, sql_connection):
    """
    Cleans addresses that have been expired for more than 10 days and notifies owners.
    
    Args:
        context: Telegram context for sending messages
        sql_connection: Database connection object
    """
    # Get addresses that are ready to be released
    expired_addresses = get_release_ready_addresses(sql_connection)
    
    if not expired_addresses:
        logger.info("Finished expired address cleaning process")
        return

    logger.info(f"Found {len(expired_addresses)} expired addresses")
    # Create a dictionary to group addresses by chat_id
    notifications = {}
    
    # Process each expired address
    for address, chat_id in expired_addresses.items():
        # Remove the address from database
        release_address_from_database(sql_connection, address)
        
        # Group addresses by chat_id for notifications
        if chat_id not in notifications:
            notifications[chat_id] = []
        notifications[chat_id].append(address)

    # Send notifications to users
    for chat_id, addresses in notifications.items():
        if len(addresses) == 1:
            message = (f"Hello! Just letting you know that your expired code "
                      f"{addresses[0]} has been automatically removed from the system "
                      f"as it has been expired for over 10 days.")
        else:
            addresses_str = "\n".join(addresses)
            message = (f"Hello! Just letting you know that your expired codes have "
                      f"been automatically removed from the system as they have been "
                      f"expired for over 10 days:\n{addresses_str}")
        
        await safe_chat(context, chat_id, message)

    logger.info("Finished expired address cleaning process")

async def expiration_notification(context, sql_connection):
    """
    Notifies the user that their address is about to expire in 3 days.
    
    Args:
        context: Telegram context for sending messages
        sql_connection: Database connection object
        address: Address to notify about
        chat_id: Chat ID to send the notification to
    """
    just_expired_addresses = get_just_expired_addresses(sql_connection)

    if not just_expired_addresses:
        return

    logger.info(f"Found {len(just_expired_addresses)} addresses that have just expired")
    # Process each expired address
    notifications = {}
    for address, chat_id in just_expired_addresses.items():
        # Group addresses by chat_id for notifications
        if chat_id not in notifications:
            notifications[chat_id] = []
        notifications[chat_id].append(address)
    
    # Send notifications to users
    for chat_id, addresses in notifications.items():
        if len(addresses) == 1:
            message = (f"Hello! Just letting you know that your code "
                      f"{addresses[0]} has just expired. It will be released automatically in 10 days.")
        else:
            addresses_str = "\n".join(addresses)
            message = (f"Hello! Just letting you know that your codes "
                      f"{addresses_str} have just expired. They will be released automatically in 10 days.")
        
        await safe_chat(context, chat_id, message)

    logger.info("Finished expiration notification process")