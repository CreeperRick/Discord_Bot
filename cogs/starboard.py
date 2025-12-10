import discord
from discord.ext import commands
from utils.db_async import DB

class Starboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="setstarboard")
    @commands.has_permissions(manage_guild=True)
    async def setstarboard(self, ctx: commands.Context, channel: discord.TextChannel, threshold:int=3):
        await DB.set_kv(ctx.guild.id, "starboard_channel", channel.id)
        await DB.set_kv(ctx.guild.id, "starboard_threshold", threshold)
        await ctx.send(f"Starboard set: {channel.mention} threshold {threshold}")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot: return
        if str(reaction.emoji) != "⭐": return
        msg = reaction.message
        guild = msg.guild
        ch_id = await DB.get_kv(guild.id, "starboard_channel", None)
        threshold = await DB.get_kv(guild.id, "starboard_threshold", 3)
        if not ch_id: return
        count = 0
        for r in msg.reactions:
            if str(r.emoji) == "⭐": count = r.count
        if count >= threshold:
            sb = guild.get_channel(ch_id)
            if not sb: return
            done = await DB.get_kv(guild.id, f"star:{msg.id}", False)
            if done: return
            embed = discord.Embed(description=msg.content or "(embed/attachment)", timestamp=msg.created_at)
            embed.set_author(name=str(msg.author), icon_url=msg.author.display_avatar.url)
            embed.add_field(name="Jump", value=f"[Jump]({msg.jump_url})")
            if msg.attachments:
                embed.set_image(url=msg.attachments[0].url)
            await sb.send(embed=embed)
            await DB.set_kv(guild.id, f"star:{msg.id}", True)

async def setup(bot):
    await bot.add_cog(Starboard(bot))
