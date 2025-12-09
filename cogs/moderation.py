# cogs/moderation.py
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

class Moderation(commands.Cog):
    """Moderation commands: kick, ban, mute, unmute, purge."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Kick
    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: Optional[str] = None):
        await member.kick(reason=reason)
        await ctx.send(f"🔨 {member} was kicked. Reason: {reason}")

    # Ban
    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, member: discord.Member, days: int = 0, *, reason: Optional[str] = None):
        await member.ban(reason=reason, delete_message_days=days)
        await ctx.send(f"⛔ {member} was banned. Reason: {reason}")

    # Clear messages
    @commands.command(name="purge", aliases=["clear"])
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx: commands.Context, limit: int = 10):
        deleted = await ctx.channel.purge(limit=limit+1)  # +1 to include command message
        await ctx.send(f"🧹 Deleted {len(deleted)-1} messages.", delete_after=5)

    # Simple role mute (requires a 'Muted' role to exist)
    @commands.command(name="mute")
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx: commands.Context, member: discord.Member, *, reason: Optional[str] = None):
        role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not role:
            # create a Muted role with send_messages disabled
            role = await ctx.guild.create_role(name="Muted", reason="Auto-created muted role")
            for ch in ctx.guild.channels:
                try:
                    await ch.set_permissions(role, send_messages=False, add_reactions=False, speak=False)
                except Exception:
                    pass
        await member.add_roles(role, reason=reason)
        await ctx.send(f"🔇 {member} has been muted.")

    @commands.command(name="unmute")
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx: commands.Context, member: discord.Member):
        role = discord.utils.get(ctx.guild.roles, name="Muted")
        if role in member.roles:
            await member.remove_roles(role)
            await ctx.send(f"🔊 {member} has been unmuted.")
        else:
            await ctx.send("That user is not muted.")

    # Add a simple slash command wrapper example for kick
    @app_commands.command(name="kick", description="Kick a member from the guild")
    @app_commands.checks.has_permissions(kick_members=True)
    async def slash_kick(self, interaction: discord.Interaction, member: discord.Member, reason: Optional[str] = None):
        await interaction.response.defer()
        await member.kick(reason=reason)
        await interaction.followup.send(f"🔨 {member} was kicked. Reason: {reason}")

    # Error handlers
    @kick.error
    async def kick_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to use this command.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Usage: kick <member> [reason]")
        else:
            await ctx.send("An error occurred.")

async def setup(bot):
    await bot.add_cog(Moderation(bot))
