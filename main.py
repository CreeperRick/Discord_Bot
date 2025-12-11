import os, logging, asyncio
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
OWNER_ID = int(os.getenv('OWNER_ID') or 0)
WEB_SECRET = os.getenv('WEB_SECRET','change-me')
WEB_PORT = int(os.getenv('WEB_PORT', '5000'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('slash_bot')

intents = discord.Intents.default()
intents.members = True
intents.message_content = False  # slash-only
intents.reactions = True

bot = commands.Bot(command_prefix='/', intents=intents, owner_id=OWNER_ID, help_command=None)

async def load_cogs():
    import os
    for f in os.listdir('./cogs'):
        if f.endswith('.py') and not f.startswith('_'):
            try:
                await bot.load_extension(f'cogs.{f[:-3]}')
                logger.info(f'Loaded cogs.{f[:-3]}')
            except Exception:
                logger.exception(f'Failed to load cogs.{f[:-3]}')

@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
    try:
        await bot.tree.sync()
        logger.info('Synced application commands.')
    except Exception:
        logger.exception('Failed to sync app commands.')
    bot.loop.create_task(start_web_ui())

async def start_web_ui():
    from web_ui import create_app
    import aiohttp.web
    app = create_app(bot, secret=WEB_SECRET)
    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    site = aiohttp.web.TCPSite(runner, '0.0.0.0', WEB_PORT)
    await site.start()
    logger.info(f'Web UI running at http://0.0.0.0:{WEB_PORT}')

async def main():
    async with bot:
        await load_cogs()
        if not TOKEN:
            logger.error('BOT_TOKEN not set. Set it in .env or Replit secrets.')
        await bot.start(TOKEN)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Shutting down.')
