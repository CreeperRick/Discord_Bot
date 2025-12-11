from discord import app_commands, Interaction
from discord.ext import commands
import discord
from utils.db_async import DB

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='ticket', description='Open a ticket channel')
    async def ticket(self, interaction: Interaction, reason: str = 'No reason'):
        guild = interaction.guild
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        ch = await guild.create_text_channel(f'ticket-{interaction.user.display_name}', overwrites=overwrites, reason='Ticket opened')
        tid = await DB.create_ticket(guild.id, ch.id, interaction.user.id)
        await interaction.response.send_message(f'Ticket created: {ch.mention}', ephemeral=True)
        await ch.send(f'{interaction.user.mention} opened ticket: {reason}')

    @app_commands.command(name='close_ticket', description='Close the current ticket channel')
    @app_commands.checks.has_permissions(manage_channels=True)
    async def close_ticket(self, interaction: Interaction):
        ch = interaction.channel
        await DB.close_ticket(ch.id)
        await interaction.response.send_message('Ticket closed. Channel will be deleted in 5s.', ephemeral=True)
        try:
            await ch.delete(reason='Ticket closed via slash')
        except:
            pass

async def setup(bot):
    await bot.add_cog(Tickets(bot))
