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
WEB_SECRET = os.getenv("WEB_SECRET", "change-me")
WEB_PORT = int(os.getenv("WEB_PORT", "5000"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bot")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True

bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents,
    help_command=commands.DefaultHelpCommand(dm_help=True),
    owner_id=OWNER_ID,
)

@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user} (id: {bot.user.id})")
    try:
        await bot.tree.sync()
        logger.info("Application commands synced.")
    except Exception as e:
        logger.exception("Failed to sync app commands: %s", e)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{PREFIX}help"))

async def load_cogs():
    import os
    for fname in os.listdir("./cogs"):
        if fname.endswith(".py") and not fname.startswith("_"):
            ext = f"cogs.{fname[:-3]}"
            try:
                await bot.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception:
                logger.exception(f"Failed to load {ext}")

async def start_web_ui():
    from web_ui import create_web_app
    import aiohttp.web
    app = create_web_app(bot, secret=WEB_SECRET)
    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    site = aiohttp.web.TCPSite(runner, "0.0.0.0", WEB_PORT)
    await site.start()
    logger.info(f"Web UI started on http://0.0.0.0:{WEB_PORT}")

async def main():
    async with bot:
        await load_cogs()
        bot.loop.create_task(start_web_ui())
        if not TOKEN:
            logger.error("BOT_TOKEN is not set. Set it in the .env or Replit secrets.")
        await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown requested.")
