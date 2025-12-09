# cogs/troll.py
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random

class Troll(commands.Cog):
    """Harmless troll commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # -------------------------------------------
    # 1. Fake Ban (prefix)
    # -------------------------------------------
    @commands.command(name="fakeban")
    async def fakeban(self, ctx, member: discord.Member = None):
        if member is None:
            return await ctx.send("Usage: fakeban <member>")
        
        embed = discord.Embed(
            title="User Banned",
            description=f"{member.mention} has been permanently banned from the server.",
            color=discord.Color.red()
        )
        embed.set_footer(text="(totally legit ban, trust me)")
        await ctx.send(embed=embed)

    # -------------------------------------------
    # 2. Mock Text (prefix)
    # -------------------------------------------
    @commands.command(name="mock")
    async def mock(self, ctx, *, text: str):
        mocked = "".join(
            c.upper() if random.choice([True, False]) else c.lower()
            for c in text
        )
        await ctx.send(mocked)

    # -------------------------------------------
    # 3. Reverse someone's last message
    # -------------------------------------------
    @commands.command(name="reverse")
    async def reverse(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        
        # Fetch last non-command message
        async for msg in ctx.channel.history(limit=50):
            if msg.author == member and msg.content and not msg.content.startswith(ctx.prefix):
                reversed_text = msg.content[::-1]
                return await ctx.send(f"🔄 **{member.display_name} said:** `{reversed_text}`")

        await ctx.send("Couldn't find a message to reverse!")

    # -------------------------------------------
    # 4. Ping Spam (SLASH COMMAND)
    # -------------------------------------------
    @app_commands.command(name="pingspam", description="Lightly troll someone with pings.")
    @app_commands.describe(member="Who you want to troll")
    async def pingspam(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.send_message(f"Trolling {member.mention}… 😈")

        # Light and safe spam (5 pings)
        for _ in range(5):
            await interaction.channel.send(f"{member.mention} 👋")
            await asyncio.sleep(1.2)

    # Cooldown for the ping spam (global)
    @pingspam.error
    async def pingspam_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f"Slow down! Try again in {error.retry_after:.1f} seconds.",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Troll(bot))
