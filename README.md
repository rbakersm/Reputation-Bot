# Reputation Bot
This is a Discord bot that stores, updates, and fetches user information community reported feedback for marketplace transactions.
Utilizes the Discord.py library to interact with the users and the discord api.
Utilizes Mongodb to host the database

## Technologies used
-[Python 3.11](https://www.python.org/downloads/release/python-3110/)
-[Discord.py](https://discordpy.readthedocs.io/en/stable/)
-[Mongodb](https://www.mongodb.com/)

## How to use
1. Install Python 3.11
2. Install discord.py
3. Install [pymongo](https://pymongo.readthedocs.io/en/stable/installation.html)
4. Create a new discord bot [application](https://discord.com/developers/applications)
5. Install dotenv
6. In a .env file, assign your discord bot auth token as TOKEN={token}, the mongodb client connection link as CLIENT={client}, and your 18-digit discord id as ADMIN_ID={admin_id}
8. Set Message Content Intent in your application to on
10. Replace the database and collection name with your names
