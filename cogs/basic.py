# cogs/basic.py
import discord
from discord.ext import commands
from discord import app_commands
import time

class Basic(commands.Cog):
    """Basic utility commands: ping, info, avatar, userinfo."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # prefix command
    @commands.command(name="ping")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def ping(self, ctx: commands.Context):
        """Shows bot latency"""
        started = time.perf_counter()
        msg = await ctx.send("Pong... measuring latency")
        elapsed = (time.perf_counter() - started) * 1000
        embed = discord.Embed(title="Pong!", color=discord.Color.blurple())
        embed.add_field(name="Websocket latency", value=f"{round(self.bot.latency*1000)}ms")
        embed.add_field(name="REST roundtrip", value=f"{int(elapsed)}ms")
        await msg.edit(content=None, embed=embed)

    # slash command equivalent
    @app_commands.command(name="ping", description="Check bot latency")
    async def slash_ping(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await interaction.followup.send(f"Pong! {round(self.bot.latency*1000)}ms")

    @commands.command(name="userinfo", aliases=["uinfo"])
    async def userinfo(self, ctx: commands.Context, member: discord.Member = None):
        member = member or ctx.author
        embed = discord.Embed(title=f"{member}", color=member.color)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="ID", value=member.id)
        embed.add_field(name="Joined", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S") if member.joined_at else "N/A")
        embed.add_field(name="Created", value=member.created_at.strftime("%Y-%m-%d %H:%M:%S"))
        await ctx.send(embed=embed)

    @app_commands.command(name="userinfo", description="Get info about a user")
    @app_commands.describe(member="Member to lookup")
    async def slash_userinfo(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        embed = discord.Embed(title=f"{member}", color=member.color)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="ID", value=member.id)
        embed.add_field(name="Joined", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S") if member.joined_at else "N/A")
        embed.add_field(name="Created", value=member.created_at.strftime("%Y-%m-%d %H:%M:%S"))
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Basic(bot))
