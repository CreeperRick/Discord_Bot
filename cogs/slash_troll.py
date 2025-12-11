from discord import app_commands, Interaction
from discord.ext import commands
import random, asyncio
from utils.db_async import DB

class Troll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='ghost_ping', description='Send a short ghost ping')
    async def ghost_ping(self, interaction: Interaction, member: discord.Member):
        enabled = await DB.get_kv(interaction.guild.id, 'troll_enabled', True)
        if not enabled:
            return await interaction.response.send_message('Troll disabled', ephemeral=True)
        m = await interaction.channel.send(f'{member.mention}')
        await asyncio.sleep(1)
        try: await m.delete()
        except: pass
        await interaction.response.send_message('Ghosted', ephemeral=True)

async def setup(bot):
    await bot.add_cog(Troll(bot))
