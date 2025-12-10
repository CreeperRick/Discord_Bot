import discord
from discord.ext import commands
from utils.db_async import DB
import time, re

class AutoMod(commands.Cog):
    """Basic automod: blacklist words, link filtering, caps filter, simple anti-spam."""

    def __init__(self, bot):
        self.bot = bot
        self._last_messages = {}

    @commands.command(name="setfilter")
    @commands.has_permissions(manage_guild=True)
    async def setfilter(self, ctx: commands.Context, filter_type: str, *, value: str = ""):
        if filter_type == "blacklist":
            words = [w.strip().lower() for w in value.split(",") if w.strip()]
            await DB.set_kv(ctx.guild.id, "blacklist_words", words)
            return await ctx.send(f"Blacklist set: {words}")
        if filter_type == "links":
            enabled = value.lower() in ("true","1","on","yes")
            await DB.set_kv(ctx.guild.id, "links_filter", enabled)
            return await ctx.send(f"Links filter set to {enabled}")
        if filter_type == "caps":
            try:
                thr = int(value)
                await DB.set_kv(ctx.guild.id, "caps_threshold", thr)
                return await ctx.send(f"Caps threshold set to {thr}%")
            except:
                return await ctx.send("Usage: setfilter caps <percentage>")
        await ctx.send("Unknown filter type.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        guild_id = message.guild.id
        content = message.content or ""
        bl = await DB.get_kv(guild_id, "blacklist_words", [])
        for w in bl:
            if w.lower() in content.lower():
                try:
                    await message.delete()
                except:
                    pass
                await DB.add_modlog(guild_id, "automod_delete", 0, message.author.id, f"blacklist matched {w}", int(time.time()))
                return
        links_enabled = await DB.get_kv(guild_id, "links_filter", False)
        if links_enabled and re.search(r"https?://", content):
            try:
                await message.delete()
            except:
                pass
            await DB.add_modlog(guild_id, "automod_delete", 0, message.author.id, "links", int(time.time()))
            return
        thr = await DB.get_kv(guild_id, "caps_threshold", 0)
        if thr > 0 and len(content) >= 5:
            alpha = sum(1 for c in content if c.isalpha())
            if alpha > 0:
                upper = sum(1 for c in content if c.isupper())
                pct = upper / alpha * 100
                if pct >= thr:
                    try:
                        await message.delete()
                    except:
                        pass
                    await DB.add_modlog(guild_id, "automod_delete", 0, message.author.id, f"caps {int(pct)}%", int(time.time()))
                    return
        key = (guild_id, message.author.id)
        last = self._last_messages.get(key)
        now = time.time()
        if last:
            ts, txt = last
            if txt == content and now - ts < 4:
                try:
                    await message.delete()
                except:
                    pass
                return
        self._last_messages[key] = (now, content)

async def setup(bot):
    await bot.add_cog(AutoMod(bot))
