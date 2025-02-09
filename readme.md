# BiisiToiveBot

A Telegram bot for managing song requests between users and event organizers/DJs.

## Features

- Simple song request system
- Code-based recipient management
- Recipient support for both private and group chats (for example a group of djs in an event)
- Automatic code expiration and cleanup

## Usage

### For Users (Requesters)
1. Start a private chat with the bot and use `/start` to register
2. Use `/koodi` to set a recipient using their event code
3. Send song requests with `/biisitoive`
4. Change your nickname with `/nikki`

### For Recipients (DJs/Organizers)
1. Use `/vastaanottaja` to register your chat as a recipient
2. Create new recipient codes with `/uusi`
3. Manage your codes:
    - `/omat` - View all your codes (active/inactive/expired)
    - `/onoff` - Toggle code status (active/inactive)
    - `/vanhenna` - Expire a code (expired codes will be released after 10 days)
    - `/vapauta` - Delete and release a code

## Technical Details
- Codes always have an expiration date
- Expired codes are automatically released after 10 days
- Expired codes can be renewed
- One chat can be both a user and a recipient
- Recipients can be private or group chats
- User can only be private chats

## Installation and running
### Terminal
```
cd songrequestbot
pip install -r requirements.txt
export BOT_TOKEN='token'
export LANGUAGE='fi' # 'fi' is the only option currently implemented
python3 bot.py
```

### Docker
Keep the database inside container:
```
cd songrequestbot
docker build -t songrequestbot .
docker run --name songrequestbot -e BOT_TOKEN='token' -e BOT_LANGUAGE='fi' songrequestbot
```

Database exists on another volume (make sure the rw permissions are correct for the database):
```
cd songrequestbot
docker build -t songrequestbot .
docker run -v /path/to/database/:/app/database/:rw --name songrequestbot -e BOT_TOKEN='token' -e BOT_LANGUAGE='fi' songrequestbot
```

## Future Development
Contributions are welcome! Some planned features include:

- Proper multilanguage support
- Song request statistics
- Request frequency analytics
- Hourly request graphs

## Utilities

### Botfather commands
Finnish:
```
start - Rekisteröidy käyttäjäksi
koodi - Aseta vastaanottajan koodi
biisitoive - Lähetä biisitoive vastaanottajalle
nikki - Päivitä lempinimesi
vastaanottaja - Rekisteröi nykyinen chat vastaanottajaksi
uusi - Liitä uusi koodi tähän chattiin
omat - Näytä tähän chattiin liitetyt koodit
onoff - Aseta koodi päälle/pois
vanhenna - Vanhenna koodi
uudista - Uudista vannhentunut koodi
vapauta - Vapauta koodi
cancel - Peru mikä tahansa operaatio
apua - Ohjeita
```
English:
-TBD

## Contributing
Feel free to submit issues and pull requests to help improve the bot!
