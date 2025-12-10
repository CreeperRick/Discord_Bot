# cogs/moderation_advanced.py
import discord
from discord.ext import commands, tasks
from discord import app_commands
import time
import asyncio
from utils.db_async import DB

class ModerationAdvanced(commands.Cog):
    """Advanced moderation: tempban/tempmute, modlogs, automod basic"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._temp_tasks = {}
        self.reminder_task = tasks.loop(seconds=30)(self._reminder_worker)
        self.reminder_task.start()

    def cog_unload(self):
        self.reminder_task.cancel()
        for t in self._temp_tasks.values():
            t.cancel()

    # helper: ensure modlog channel exists or send to guild system channel
    async def _log_action(self, guild: discord.Guild, embed: discord.Embed):
        # try to fetch mod-log channel from DB
        ml = await DB.get_kv(guild.id, "modlog_channel", None)
        channel = None
        if ml:
            channel = guild.get_channel(ml)
        if not channel and guild.system_channel:
            channel = guild.system_channel
        if channel:
            try:
                await channel.send(embed=embed)
            except Exception:
                pass

    @commands.command(name="setmodlog")
    @commands.has_permissions(manage_guild=True)
    async def setmodlog(self, ctx: commands.Context, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        await DB.set_kv(ctx.guild.id, "modlog_channel", channel.id)
        await ctx.send(f"Modlog channel set to {channel.mention}")

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, member: discord.Member, days:int=0, *, reason:str=None):
        await member.ban(reason=reason, delete_message_days=days)
        await DB.add_modlog(ctx.guild.id, "ban", ctx.author.id, member.id, reason or "", int(time.time()))
        embed = discord.Embed(title="Member Banned", color=discord.Color.red())
        embed.add_field(name="User", value=str(member))
        embed.add_field(name="By", value=str(ctx.author))
        embed.add_field(name="Reason", value=reason or "No reason")
        await self._log_action(ctx.guild, embed)
        await ctx.send(f"⛔ {member} banned.")

    @commands.command(name="tempban")
    @commands.has_permissions(ban_members=True)
    async def tempban(self, ctx: commands.Context, member: discord.Member, seconds:int, *, reason:str=None):
        await member.ban(reason=reason)
        await DB.add_modlog(ctx.guild.id, "tempban", ctx.author.id, member.id, reason or "", int(time.time()))
        await ctx.send(f"⛔ {member} temporarily banned for {seconds} seconds.")
        # schedule unban
        async def unban_later(guild_id, user_id, delay):
            await asyncio.sleep(delay)
            g = self.bot.get_guild(guild_id)
            if not g:
                return
            try:
                await g.unban(discord.Object(id=user_id))
            except Exception:
                pass
        t = self.bot.loop.create_task(unban_later(ctx.guild.id, member.id, seconds))
        self._temp_tasks[f"tempban:{ctx.guild.id}:{member.id}"] = t

    @commands.command(name="tempmute")
    @commands.has_permissions(manage_roles=True)
    async def tempmute(self, ctx: commands.Context, member: discord.Member, seconds:int, *, reason:str=None):
        role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not role:
            role = await ctx.guild.create_role(name="Muted", reason="Auto-created by tempmute")
            for ch in ctx.guild.channels:
                try:
                    await ch.set_permissions(role, send_messages=False, add_reactions=False, speak=False)
                except Exception:
                    pass
        await member.add_roles(role, reason=reason)
        await DB.add_modlog(ctx.guild.id, "tempmute", ctx.author.id, member.id, reason or "", int(time.time()))
        await ctx.send(f"🔇 {member} muted for {seconds} seconds.")
        async def unmute_later(guild_id, user_id, delay):
            await asyncio.sleep(delay)
            g = self.bot.get_guild(guild_id)
            if not g:
                return
            m = g.get_member(user_id)
            if not m:
                return
            r = discord.utils.get(g.roles, name="Muted")
            if r in m.roles:
                try:
                    await m.remove_roles(r)
                except Exception:
                    pass
        t = self.bot.loop.create_task(unmute_later(ctx.guild.id, member.id, seconds))
        self._temp_tasks[f"tempmute:{ctx.guild.id}:{member.id}"] = t

    @commands.command(name="modlog")
    @commands.has_permissions(view_audit_log=True)
    async def modlog(self, ctx: commands.Context, limit:int=20):
        rows = await DB.get_modlog(ctx.guild.id, limit=limit)
        if not rows:
            await ctx.send("No modlog entries.")
            return
        embed = discord.Embed(title="Modlog", color=discord.Color.blurple())
        for r in rows:
            ts = r["timestamp"]
            embed.add_field(name=f'{r["id"]} {r["action"]}',
                            value=f'By <@{r["moderator_id"]}> on <@{r["target_id"]}> — {r["reason"]} ({ts})',
                            inline=False)
        await ctx.send(embed=embed)

    # automod skeleton (bad words)
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        banned = await DB.get_kv(message.guild.id, "blacklist_words", [])
        if not banned:
            return
        content = message.content.lower()
        for w in banned:
            if w.lower() in content:
                try:
                    await message.delete()
                except Exception:
                    pass
                await DB.add_modlog(message.guild.id, "automod_delete", 0, message.author.id, f"matched {w}", int(time.time()))
                ch = await DB.get_kv(message.guild.id, "modlog_channel", None)
                if ch:
                    c = message.guild.get_channel(ch)
                    if c:
                        await c.send(f"Auto-deleted message by {message.author.mention} matching `{w}`")
                return

    # admin command to set blacklist
    @commands.command(name="blacklist")
    @commands.has_permissions(manage_guild=True)
    async def blacklist(self, ctx: commands.Context, action:str, *, words:str):
        # usage: !blacklist add badword1,badword2   or remove badword
        current = await DB.get_kv(ctx.guild.id, "blacklist_words", [])
        if action == "add":
            adds = [w.strip() for w in words.split(",") if w.strip()]
            combined = list(set(current + adds))
            await DB.set_kv(ctx.guild.id, "blacklist_words", combined)
            await ctx.send(f"Added: {adds}")
        elif action == "remove":
            rm = words.strip()
            new = [w for w in current if w != rm]
            await DB.set_kv(ctx.guild.id, "blacklist_words", new)
            await ctx.send(f"Removed `{rm}`")
        else:
            await ctx.send("Usage: blacklist add|remove <comma-separated>")

async def setup(bot):
    await bot.add_cog(ModerationAdvanced(bot))
