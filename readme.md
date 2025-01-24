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
    - `/poista` - Expire a code (expired codes will be released after 10 days)
    - `/vapauta` - Delete and release a code

## Technical Details
- Expired codes are automatically released after 10 days
- One chat can be both a user and a recipient
- Recipients can be private or group chats
- User can only be private chats

## Future Development
Contributions are welcome! Some planned features include:

- Proper multilanguage support
- Song request statistics
- Request frequency analytics
- Hourly request graphs

## Contributing
Feel free to submit issues and pull requests to help improve the bot!
