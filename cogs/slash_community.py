from discord import app_commands, Interaction
from discord.ext import commands
import discord
from utils.db_async import DB

class Community(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='balance', description='Show your balance')
    async def balance(self, interaction: Interaction):
        u = await DB.get_user(interaction.guild.id, interaction.user.id)
        await interaction.response.send_message(f'{interaction.user.mention} — Balance: {u["balance"]} coins', ephemeral=True)

    @app_commands.command(name='pay', description='Pay a member coins')
    async def pay(self, interaction: Interaction, member: discord.Member, amount:int):
        if amount <= 0:
            return await interaction.response.send_message('Amount must be positive.', ephemeral=True)
        bal = (await DB.get_user(interaction.guild.id, interaction.user.id))['balance']
        if bal < amount:
            return await interaction.response.send_message('Insufficient funds.', ephemeral=True)
        await DB.add_balance(interaction.guild.id, interaction.user.id, -amount)
        await DB.add_balance(interaction.guild.id, member.id, amount)
        await interaction.response.send_message(f'Transferred {amount} to {member.mention}', ephemeral=True)

    @app_commands.command(name='rank', description='Show your level')
    async def rank(self, interaction: Interaction, member: discord.Member = None):
        member = member or interaction.user
        u = await DB.get_user(interaction.guild.id, member.id)
        await interaction.response.send_message(f'{member.display_name} — Level {u["level"]} ({u["xp"]} xp)', ephemeral=True)

async def setup(bot):
    await bot.add_cog(Community(bot))
