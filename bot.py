from telegram import Update
from telegram.ext import Application, CommandHandler, CommandHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio

from utils.config import BOT_TOKEN, LANGUAGE, sql_connection
from utils.logger import get_logger
from utils.cleaner import clean_expired_addresses, expiration_notification
import command_handlers as handlers
from db.schema import create_tables

logger = get_logger(__name__)

async def scheduled_jobs(application):
    # --- Add database cleaning jobs ---
    scheduler = AsyncIOScheduler()
    scheduler.add_job(clean_expired_addresses, 'interval', hours=1, args=[application, sql_connection])
    scheduler.add_job(expiration_notification, 'interval', hours=1, args=[application, sql_connection])
    scheduler.start()

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(BOT_TOKEN).build()

    # Create database tables if they don't exist
    create_tables(sql_connection)

    # --- Add command handlers based on language ---
    if LANGUAGE == 'en':
        logger.error('Language not implemented')
        return
    elif LANGUAGE == 'fi':
        # Käyttäjän kommennot
        application.add_handler(CommandHandler("apua", handlers.help_message)) # Help message

        # Vastaanottajan komennot
        application.add_handler(CommandHandler("vastaanottaja", handlers.register_recipient)) # Luo uusi vastaanottajatunnus
        application.add_handler(CommandHandler("omat", handlers.list_addresses)) # Näytä kaikki omat luodut koodit
        application.add_handler(CommandHandler("jarjestaja_apu", handlers.recipient_help_message)) # Luo uusi koodi
    
        # TODO
        # application.add_handler(CommandHandler("block", handlers.block_sender)) # Blokkaa lähettäjä (in case spam)

    else:
        logger.error('Unsupported language specified, exiting')
        return

    # --- Add conversation handlers to application ---

    # User registeration
    register_conv_handler = handlers.get_register_conv_handler()
    application.add_handler(register_conv_handler)

    # Set recipient
    set_recipient_conv_handler = handlers.get_set_recipient_conv_handler()
    application.add_handler(set_recipient_conv_handler)

    # Song request
    song_request_conv_handler = handlers.get_song_request_conv_handler()
    application.add_handler(song_request_conv_handler)

    # Address creation
    create_address_conv_handler = handlers.get_create_address_conv_handler()
    application.add_handler(create_address_conv_handler)

    # Address removal
    remove_address_conv_handler = handlers.get_remove_address_conv_handler()
    application.add_handler(remove_address_conv_handler)

    # Toggle address on/off
    toggle_address_conv_handler = handlers.get_toggle_address_conv_handler()
    application.add_handler(toggle_address_conv_handler)

    # Release address
    release_address_conv_handler = handlers.get_release_address_conv_handler()
    application.add_handler(release_address_conv_handler)

    # Renew address
    renew_address_conv_handler = handlers.get_renew_address_conv_handler()
    application.add_handler(renew_address_conv_handler)

    # Update nickname
    update_nickname_conv_handler = handlers.get_change_nickname_conv_handler()
    application.add_handler(update_nickname_conv_handler)

    # --- Run scheduled jobs ---
    asyncio.get_event_loop().create_task(scheduled_jobs(application))

    # --- Run the bot until the user presses Ctrl-C ---
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
