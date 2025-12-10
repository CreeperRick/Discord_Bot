# cogs/utility.py
import discord
from discord.ext import commands, tasks
from discord import app_commands
import time
from utils.db_async import DB
import asyncio

class Utility(commands.Cog):
    """Utility features: polls, afk, reminders, server stats"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.reminder_worker.start()

    def cog_unload(self):
        self.reminder_worker.cancel()

    @commands.command(name="poll")
    async def poll(self, ctx: commands.Context, *, question: str):
        emb = discord.Embed(title="Poll", description=question, color=discord.Color.blurple())
        m = await ctx.send(embed=emb)
        await m.add_reaction("👍")
        await m.add_reaction("👎")
        await m.add_reaction("🤷")
        await ctx.send("Poll created. React to vote!")

    # AFK
    @commands.command(name="afk")
    async def afk(self, ctx: commands.Context, *, note:str="Away"):
        await DB.set_afk(ctx.guild.id, ctx.author.id, note, int(time.time()))
        await ctx.send(f"{ctx.author.mention} is now AFK: {note}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        # clear AFK if present
        afk = await DB.get_afk(message.guild.id, message.author.id)
        if afk:
            await DB.remove_afk(message.guild.id, message.author.id)
            await message.channel.send(f"Welcome back, {message.author.mention}. AFK cleared.")
        # notify when mentioning someone AFK
        for user in message.mentions:
            afk = await DB.get_afk(message.guild.id, user.id)
            if afk:
                await message.channel.send(f"{user.display_name} is AFK: {afk['note']} (since {afk['since']})")

    # Reminders
    @commands.command(name="remindme")
    async def remindme(self, ctx: commands.Context, seconds: int, *, content:str):
        ts = int(time.time()) + seconds
        await DB.add_reminder(ctx.guild.id, ctx.author.id, content, ts)
        await ctx.send(f"Okay {ctx.author.mention}, I'll remind you in {seconds} seconds.")

    @tasks.loop(seconds=20)
    async def reminder_worker(self):
        now = int(time.time())
        rows = await DB.get_due_reminders(now)
        for row in rows:
            rid, guild_id, user_id, content = row
            g = self.bot.get_guild(guild_id)
            if not g:
                await DB.delete_reminder(rid)
                continue
            member = g.get_member(user_id)
            if member:
                try:
                    await member.send(f"Reminder: {content}")
                except Exception:
                    # cannot DM
                    channel = g.system_channel or next((c for c in g.text_channels if c.permissions_for(g.me).send_messages), None)
                    if channel:
                        await channel.send(f"{member.mention} Reminder: {content}")
            await DB.delete_reminder(rid)

    @commands.command(name="serverstats")
    async def serverstats(self, ctx: commands.Context):
        g = ctx.guild
        channels = len(g.channels)
        roles = len(g.roles)
        members = g.member_count
        emojis = len(g.emojis)
        embed = discord.Embed(title=f"Stats for {g.name}", color=discord.Color.green())
        embed.add_field(name="Members", value=str(members))
        embed.add_field(name="Channels", value=str(channels))
        embed.add_field(name="Roles", value=str(roles))
        embed.add_field(name="Emojis", value=str(emojis))
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Utility(bot))
