import discord
from discord.ext import commands
from utils.db_async import DB
import time

class Tickets(commands.Cog):
    """Simple ticket system using private channels."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ticket")
    async def ticket(self, ctx: commands.Context, *, reason: str = "No reason"):
        guild = ctx.guild
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        ch = await guild.create_text_channel(f"ticket-{ctx.author.display_name}", overwrites=overwrites, reason="Ticket opened")
        now = int(time.time())
        conn = await DB.get_conn()
        cur = await conn.execute("INSERT INTO tickets (guild_id, channel_id, user_id, status, created_at) VALUES (?, ?, ?, ?, ?)", (guild.id, ch.id, ctx.author.id, "open", now))
        await conn.commit()
        await ctx.send(f"Ticket created: {ch.mention}")
        await ch.send(f"{ctx.author.mention} opened a ticket: {reason}")

    @commands.command(name="close")
    @commands.has_permissions(manage_channels=True)
    async def close(self, ctx: commands.Context):
        ch = ctx.channel
        conn = await DB.get_conn()
        cur = await conn.execute("SELECT id FROM tickets WHERE channel_id=?", (ch.id,))
        row = await cur.fetchone()
        if not row:
            return await ctx.send("This channel is not a ticket.")
        await conn.execute("UPDATE tickets SET status=? WHERE channel_id=?", ("closed", ch.id))
        await conn.commit()
        await ch.send("Ticket closed. Channel will be deleted in 10s.")
        try:
            await asyncio.sleep(10)
            await ch.delete(reason="Ticket closed")
        except:
            pass

async def setup(bot):
    await bot.add_cog(Tickets(bot))
