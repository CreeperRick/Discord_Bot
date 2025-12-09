# main.py
import os
import logging
import asyncio
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
PREFIX = os.getenv("PREFIX", "!")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("discord_bot")

# Intents: we enable members and message content for typical bot features.
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True

# Bot instance with command tree (slash commands) support
bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents,
    help_command=commands.DefaultHelpCommand(dm_help=True),
    owner_id=OWNER_ID,
)

# On ready - sync slash commands and print info
@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        # Sync global application commands (slash commands)
        await bot.tree.sync()
        logger.info("Synced application commands (slash commands).")
    except Exception as e:
        logger.exception("Failed to sync app commands: %s", e)
    activity = discord.Activity(type=discord.ActivityType.watching, name=f"{PREFIX}help")
    await bot.change_presence(activity=activity)

# Auto-load cogs from cogs/ folder
async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and not filename.startswith("_"):
            ext = f"cogs.{filename[:-3]}"
            try:
                await bot.load_extension(ext)
                logger.info(f"Loaded extension {ext}")
            except Exception as e:
                logger.exception(f"Failed to load extension {ext}: {e}")

async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutting down (KeyboardInterrupt).")
