# cogs/events.py
import discord
from discord.ext import commands
from discord import app_commands

class Events(commands.Cog):
    """Handles join/leave, basic reaction role example, message logging hook."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        # Try to find a general/welcome channel
        guild = member.guild
        channel = discord.utils.find(lambda c: c.name.startswith("welcome") or c.name == "general", guild.text_channels)
        if channel:
            await channel.send(f"Welcome to the server, {member.mention}! Please read the rules.")
        # Optionally assign a default role
        default_role = discord.utils.get(guild.roles, name="Member")
        if default_role:
            try:
                await member.add_roles(default_role, reason="Auto role on join")
            except Exception:
                pass

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        channel = discord.utils.find(lambda c: c.name.startswith("welcome") or c.name == "general", member.guild.text_channels)
        if channel:
            await channel.send(f"{member} has left the server.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Allow commands to run
        if message.author.bot:
            return
        await self.bot.process_commands(message)

    # Reaction role skeleton - needs configuration to be useful
    @commands.command(name="reactionrole")
    @commands.has_permissions(manage_roles=True)
    async def reactionrole(self, ctx: commands.Context):
        msg = await ctx.send("React to get the role: 🎮 -> Gamer")
        await msg.add_reaction("🎮")
        await ctx.send("Set up: reaction role message posted (example).")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        # Example: if message id matches and emoji matches, add role
        # This function is a stub — wire it with persistent IDs for production.
        pass

async def setup(bot):
    await bot.add_cog(Events(bot))
