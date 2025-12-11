from discord import app_commands, Interaction
from discord.ext import commands
import discord
from utils.db_async import DB

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='ban', description='Ban a member')
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: Interaction, member: discord.Member, reason: str = None):
        await member.ban(reason=reason)
        await DB.add_mod(interaction.guild.id, 'ban', interaction.user.id, member.id, reason or '')
        await interaction.response.send_message(f'⛔ {member.display_name} has been banned.', ephemeral=True)

    @app_commands.command(name='kick', description='Kick a member')
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: Interaction, member: discord.Member, reason: str = None):
        await member.kick(reason=reason)
        await DB.add_mod(interaction.guild.id, 'kick', interaction.user.id, member.id, reason or '')
        await interaction.response.send_message(f'🔨 {member.display_name} has been kicked.', ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
