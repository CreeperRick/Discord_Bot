# cogs/starboard.py
import discord
from discord.ext import commands
from utils.db_async import DB

class Starboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="setstarboard")
    @commands.has_permissions(manage_guild=True)
    async def setstarboard(self, ctx, channel: discord.TextChannel, threshold: int = 3):
        await DB.set_kv(ctx.guild.id, "starboard_channel", channel.id)
        await DB.set_kv(ctx.guild.id, "starboard_threshold", threshold)
        await ctx.send(f"Starboard set to {channel.mention} with threshold {threshold}")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return
        if str(reaction.emoji) != "⭐":
            return
        msg = reaction.message
        guild = msg.guild
        ch_id = await DB.get_kv(guild.id, "starboard_channel", None)
        threshold = await DB.get_kv(guild.id, "starboard_threshold", 3)
        if not ch_id:
            return
        count = 0
        for react in msg.reactions:
            if str(react.emoji) == "⭐":
                count = react.count
        if count >= threshold:
            sb_chan = guild.get_channel(ch_id)
            if not sb_chan:
                return
            # avoid duplicating starboard post
            existing = await DB.get_kv(guild.id, f"star:{msg.id}", None)
            if existing:
                # update existing
                return
            embed = discord.Embed(title=f"⭐ {count} | {msg.author}", description=msg.content or "(embed/attachment)", timestamp=msg.created_at)
            embed.add_field(name="Jump", value=f"[Jump to message]({msg.jump_url})")
            if msg.attachments:
                embed.set_image(url=msg.attachments[0].url)
            await sb_chan.send(embed=embed)
            await DB.set_kv(guild.id, f"star:{msg.id}", True)

async def setup(bot):
    await bot.add_cog(Starboard(bot))
