import discord
from discord.ext import commands, tasks
from utils.db_async import DB
import random, time

class Community(commands.Cog):
    """Economy, leveling, leaderboards."""

    def __init__(self, bot):
        self.bot = bot
        self.xp_task.start()

    def cog_unload(self):
        self.xp_task.cancel()

    @commands.command(name="balance", aliases=["bal"])
    async def balance(self, ctx: commands.Context):
        bal = await DB.get_balance(ctx.guild.id, ctx.author.id)
        await ctx.send(f"{ctx.author.mention} — Balance: {bal} coins")

    @commands.command(name="pay")
    async def pay(self, ctx: commands.Context, member: discord.Member, amount:int):
        if amount <= 0:
            return await ctx.send("Must be positive.")
        bal = await DB.get_balance(ctx.guild.id, ctx.author.id)
        if bal < amount:
            return await ctx.send("Insufficient funds.")
        await DB.add_balance(ctx.guild.id, ctx.author.id, -amount)
        await DB.add_balance(ctx.guild.id, member.id, amount)
        await ctx.send(f"Sent {amount} to {member.mention}.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        amt = random.randint(5,12)
        conn = await DB.get_conn()
        cur = await conn.execute("SELECT xp, level FROM leveling WHERE guild_id=? AND user_id=?", (message.guild.id, message.author.id))
        row = await cur.fetchone()
        if not row:
            xp = amt; level = 0
            await conn.execute("INSERT OR REPLACE INTO leveling (guild_id, user_id, xp, level) VALUES (?, ?, ?, ?)", (message.guild.id, message.author.id, xp, level))
        else:
            xp, level = row
            xp += amt
            next_xp = (level + 1) * 100
            if xp >= next_xp:
                level += 1
                xp = xp - next_xp
                try:
                    await message.channel.send(f"🎉 {message.author.mention} leveled up to {level}!")
                except:
                    pass
            await conn.execute("UPDATE leveling SET xp=?, level=? WHERE guild_id=? AND user_id=?", (xp, level, message.guild.id, message.author.id))
        await conn.commit()
        await cur.close()

    @commands.command(name="rank")
    async def rank(self, ctx: commands.Context, member: discord.Member = None):
        member = member or ctx.author
        conn = await DB.get_conn()
        cur = await conn.execute("SELECT xp, level FROM leveling WHERE guild_id=? AND user_id=?", (ctx.guild.id, member.id))
        row = await cur.fetchone()
        await cur.close()
        if not row:
            return await ctx.send("No rank found.")
        xp, level = row
        await ctx.send(f"{member.display_name} — Level {level} ({xp} xp)")

    @tasks.loop(minutes=10)
    async def xp_task(self):
        pass

async def setup(bot):
    await bot.add_cog(Community(bot))
