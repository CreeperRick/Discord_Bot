# main.py
import os
import logging
import asyncio
from dotenv import load_dotenv

import discord
from discord.ext import commands

# load env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
PREFIX = os.getenv("PREFIX", "!")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
WEB_SECRET = os.getenv("WEB_SECRET", "change-me")  # used by web UI (keep secret)
WEB_PORT = int(os.getenv("WEB_PORT", "8080"))

# logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("discord_bot")

# intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True

# bot
bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents,
    help_command=commands.DefaultHelpCommand(dm_help=True),
    owner_id=OWNER_ID,
)

# on_ready
@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        await bot.tree.sync()
        logger.info("Synced application commands.")
    except Exception as e:
        logger.exception("Failed to sync app commands: %s", e)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{PREFIX}help"))

# auto load cogs
async def load_cogs():
    import os
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and not filename.startswith("_"):
            ext = f"cogs.{filename[:-3]}"
            try:
                await bot.load_extension(ext)
                logger.info(f"Loaded extension {ext}")
            except Exception:
                logger.exception(f"Failed to load extension {ext}")

# --- web UI runner will be started inside the bot loop ---
async def start_web_ui():
    # import here to avoid circular imports at top-level
    from web_ui import create_web_app
    app = create_web_app(bot, secret=WEB_SECRET)
    # aiohttp runner boilerplate to run within loop on port WEB_PORT
    import aiohttp.web
    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    site = aiohttp.web.TCPSite(runner, "0.0.0.0", WEB_PORT)
    await site.start()
    logger.info(f"Web UI started on http://0.0.0.0:{WEB_PORT} (secret protected)")

async def main():
    async with bot:
        # load cogs
        await load_cogs()
        # start web ui as background task
        bot.loop.create_task(start_web_ui())
        # start bot
        await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down.")
