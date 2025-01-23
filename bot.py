from telegram import Update
from telegram.ext import Application, CommandHandler, filters

from utils.config import BOT_TOKEN, LANGUAGE, sql_connection
from utils.logger import get_logger

import command_handlers as handlers

from db.schema import create_tables

logger = get_logger(__name__)

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(BOT_TOKEN).build()

    # Create database tables if they don't exist
    create_tables(sql_connection)

    # Add command handlers based on language
    if LANGUAGE == 'en':
        logger.error('Language not implemented')
        return
    elif LANGUAGE == 'fi':
        # Käyttäjän kommennot
        application.add_handler(CommandHandler("koodi", handlers.set_recipient)) # Minne viesti välitetään (tapahtuma tai esiintyjä)
        application.add_handler(CommandHandler("start", handlers.register_user)) # Rekisteröi käyttäjän
        application.add_handler(CommandHandler("biisitoive", handlers.song_request)) # Lähetä biisitoive oikealle vastaanottajalle
        

        # Vastaanottajan komennot
        application.add_handler(CommandHandler("vastaanottaja", handlers.register_recipient)) # Luo uusi vastaanottajatunnus
        application.add_handler(CommandHandler("uusi", handlers.create_address)) # Minne viesti välitetään (nykyinen chat) (pitäiskö olla vaihtoehtona automaattinen tai kustomoitu salasana)
        application.add_handler(CommandHandler("poista", handlers.remove_address)) # Poista osoite käytöstä
        application.add_handler(CommandHandler("omat", handlers.list_addresses)) # Näytä kaikki omat luodut koodit
        application.add_handler(CommandHandler("onoff", handlers.toggle_address)) # Aseta osoite jäähytilaan (ei vastaanota viestejä) tai takaisin päälle
        application.add_handler(CommandHandler("vapauta", handlers.release_address)) # Vapauta osoite (poista tietokannasta)
    
        # TODO
        # application.add_handler(CommandHandler("block", handlers.block_sender)) # Blokkaa lähettäjä (in case spam)
        # osoitteen muokkaus 

    else:
        logger.error('Unsupported language specified, exiting')
        return
    
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
