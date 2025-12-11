from discord import app_commands, Interaction
from discord.ext import commands
import random, asyncio
from utils.db_async import DB

class Troll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='ghost_ping', description='Send a short ghost ping (mention then delete)')
    async def ghost_ping(self, interaction: Interaction, member: discord.Member):
        enabled = await DB.get_kv(interaction.guild.id, 'troll_enabled', True)
        if not enabled:
            return await interaction.response.send_message('Troll features disabled in this guild.', ephemeral=True)
        m = await interaction.channel.send(f'{member.mention}')
        await asyncio.sleep(1.2)
        try: await m.delete()
        except: pass
        await interaction.response.send_message('Ghost ping sent (one-time).', ephemeral=True)

    @app_commands.command(name='mock', description='Mock text (spongebob case)')
    async def mock(self, interaction: Interaction, text: str):
        out = ''.join(c.upper() if random.choice([True,False]) else c.lower() for c in text)
        await interaction.response.send_message(out, ephemeral=False)

async def setup(bot):
    await bot.add_cog(Troll(bot))
