# cogs/economy.py
import discord
from discord.ext import commands
from utils.db_async import DB

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="balance", aliases=["bal"])
    async def balance(self, ctx):
        bal = await DB.get_balance(ctx.guild.id, ctx.author.id)
        await ctx.send(f"{ctx.author.mention} — Balance: {bal} coins")

    @commands.command(name="giveme")
    async def giveme(self, ctx, amount:int):
        # simple faucet with cooldown could be added
        new = await DB.add_balance(ctx.guild.id, ctx.author.id, amount)
        await ctx.send(f"Added {amount} coins. New balance {new}")

    @commands.command(name="pay")
    async def pay(self, ctx, member: discord.Member, amount:int):
        bal = await DB.get_balance(ctx.guild.id, ctx.author.id)
        if amount <= 0:
            return await ctx.send("Amount must be positive.")
        if bal < amount:
            return await ctx.send("Insufficient funds.")
        await DB.add_balance(ctx.guild.id, ctx.author.id, -amount)
        await DB.add_balance(ctx.guild.id, member.id, amount)
        await ctx.send(f"Transferred {amount} coins to {member.mention}.")

async def setup(bot):
    await bot.add_cog(Economy(bot))
