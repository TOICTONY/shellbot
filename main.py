from pyrogram import Client, filters


API_ID = ""
API_HASH = ""
BOT_TOKEN = ""

Shellbot = Client(
  name="shellbot",
  api_id=API_ID,
  api_hash=API_HASH,
  bot_token=BOT_TOKEN
)

print('bot was started")

Shellbot.run()    
