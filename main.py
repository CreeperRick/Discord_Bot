import discord
from discord.ext import commands
import asyncio
import logging
import os
from utils.database import Database
from utils.logger import setup_logger
import web_ui

# Setup logging
logger = setup_logger()

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents, help_command=None)
        self.db = Database()
        self.logger = logger
        
    async def setup_hook(self):
        # Load cogs
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py') and not filename.startswith('_'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    logger.info(f'Loaded cog: {filename}')
                except Exception as e:
                    logger.error(f'Failed to load cog {filename}: {e}')
        
        # Sync slash commands
        await self.tree.sync()
        logger.info('Slash commands synced!')
        
    async def on_ready(self):
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        # Start web UI
        await web_ui.start_web_server(self, self.db)

async def main():
    bot = DiscordBot()
    
    # Start bot with token from environment
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error('DISCORD_TOKEN environment variable not set!')
        return
        
    async with bot:
        await bot.start(token)

if __name__ == '__main__':
    asyncio.run(main())
