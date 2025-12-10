import discord
from discord.ext import commands
import time, asyncio
from utils.db_async import DB

class ModerationFull(commands.Cog):
    """Moderation: ban/kick/tempban/tempmute, modlog, warn, cases."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._tasks = {}

    @commands.command(name="advban")
    @commands.has_permissions(ban_members=True)
    async def advban(self, ctx: commands.Context, member: discord.Member, days:int=0, *, reason: str = None):
        await member.ban(reason=reason, delete_message_days=days)
        await DB.add_modlog(ctx.guild.id, "ban", ctx.author.id, member.id, reason or "", int(time.time()))
        await ctx.send(f"⛔ {member} banned. Reason: {reason or 'No reason'}")

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = None):
        await member.kick(reason=reason)
        await DB.add_modlog(ctx.guild.id, "kick", ctx.author.id, member.id, reason or "", int(time.time()))
        await ctx.send(f"🔨 {member} kicked.")

    @commands.command(name="tempban")
    @commands.has_permissions(ban_members=True)
    async def tempban(self, ctx: commands.Context, member: discord.Member, seconds:int, *, reason: str = None):
        await member.ban(reason=reason)
        await DB.add_modlog(ctx.guild.id, "tempban", ctx.author.id, member.id, reason or "", int(time.time()))
        await ctx.send(f"⛔ {member} temp-banned for {seconds}s.")
        async def unbanlater(gid, uid, delay):
            await asyncio.sleep(delay)
            g = self.bot.get_guild(gid)
            if not g: return
            try:
                await g.unban(discord.Object(id=uid))
            except Exception:
                pass
        t = self.bot.loop.create_task(unbanlater(ctx.guild.id, member.id, seconds))
        self._tasks[f"tempban:{ctx.guild.id}:{member.id}"] = t

    @commands.command(name="tempmute")
    @commands.has_permissions(manage_roles=True)
    async def tempmute(self, ctx: commands.Context, member: discord.Member, seconds:int, *, reason: str = None):
        role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not role:
            role = await ctx.guild.create_role(name="Muted")
            for ch in ctx.guild.channels:
                try:
                    await ch.set_permissions(role, send_messages=False, add_reactions=False, speak=False)
                except Exception:
                    pass
        await member.add_roles(role, reason=reason)
        await DB.add_modlog(ctx.guild.id, "tempmute", ctx.author.id, member.id, reason or "", int(time.time()))
        await ctx.send(f"🔇 {member} muted for {seconds}s.")
        async def unmutelater(gid, uid, delay):
            await asyncio.sleep(delay)
            g = self.bot.get_guild(gid)
            if not g: return
            m = g.get_member(uid)
            if not m: return
            r = discord.utils.get(g.roles, name="Muted")
            if r and r in m.roles:
                try:
                    await m.remove_roles(r)
                except Exception:
                    pass
        t = self.bot.loop.create_task(unmutelater(ctx.guild.id, member.id, seconds))
        self._tasks[f"tempmute:{ctx.guild.id}:{member.id}"] = t

    @commands.command(name="warn")
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason: str):
        await DB.add_modlog(ctx.guild.id, "warn", ctx.author.id, member.id, reason, int(time.time()))
        await ctx.send(f"⚠️ {member.mention} warned: {reason}")

    @commands.command(name="modlog")
    @commands.has_permissions(view_audit_log=True)
    async def modlog(self, ctx: commands.Context, limit:int=20):
        rows = await DB.get_modlog(ctx.guild.id, limit=limit)
        if not rows:
            return await ctx.send("No modlog entries.")
        embed = discord.Embed(title=f"Modlog for {ctx.guild.name}", color=discord.Color.blurple())
        for r in rows:
            embed.add_field(name=f'#{r["id"]} {r["action"]}',
                            value=f'By <@{r["moderator_id"]}> on <@{r["target_id"]}> — {r["reason"]} ({r["timestamp"]})',
                            inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ModerationFull(bot))
