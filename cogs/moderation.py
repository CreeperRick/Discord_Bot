import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime, timedelta
import time

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warnings = {}
    
    @app_commands.command(name="ban", description="Ban a user from the server")
    @app_commands.describe(user="User to ban", reason="Reason for ban")
    @app_commands.default_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
        """Ban command"""
        if user.top_role >= interaction.user.top_role:
            await interaction.response.send_message("You cannot ban someone with equal or higher role!", ephemeral=True)
            return
        
        try:
            await user.ban(reason=f"By {interaction.user}: {reason}")
            
            # Log to database
            await self.bot.db.add_moderation_log(
                interaction.guild.id,
                interaction.user.id,
                user.id,
                'ban',
                reason,
                None
            )
            
            await interaction.response.send_message(f"✅ {user.mention} has been banned. Reason: {reason}")
        except Exception as e:
            await interaction.response.send_message(f"Failed to ban user: {e}")
    
    @app_commands.command(name="kick", description="Kick a user from the server")
    @app_commands.describe(user="User to kick", reason="Reason for kick")
    @app_commands.default_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
        """Kick command"""
        if user.top_role >= interaction.user.top_role:
            await interaction.response.send_message("You cannot kick someone with equal or higher role!", ephemeral=True)
            return
        
        try:
            await user.kick(reason=f"By {interaction.user}: {reason}")
            
            # Log to database
            await self.bot.db.add_moderation_log(
                interaction.guild.id,
                interaction.user.id,
                user.id,
                'kick',
                reason,
                None
            )
            
            await interaction.response.send_message(f"👢 {user.mention} has been kicked. Reason: {reason}")
        except Exception as e:
            await interaction.response.send_message(f"Failed to kick user: {e}")
    
    @app_commands.command(name="timeout", description="Timeout a user")
    @app_commands.describe(user="User to timeout", duration="Duration (e.g., 60s, 5m, 1h, 1d)", reason="Reason for timeout")
    @app_commands.default_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, user: discord.Member, duration: str, reason: str = "No reason provided"):
        """Timeout command"""
        if user.top_role >= interaction.user.top_role:
            await interaction.response.send_message("You cannot timeout someone with equal or higher role!", ephemeral=True)
            return
        
        # Parse duration
        try:
            if duration.endswith('s'):
                seconds = int(duration[:-1])
            elif duration.endswith('m'):
                seconds = int(duration[:-1]) * 60
            elif duration.endswith('h'):
                seconds = int(duration[:-1]) * 3600
            elif duration.endswith('d'):
                seconds = int(duration[:-1]) * 86400
            else:
                seconds = int(duration)
            
            if seconds > 2419200:  # 28 days max
                await interaction.response.send_message("Duration cannot exceed 28 days!")
                return
                
            timeout_until = datetime.utcnow() + timedelta(seconds=seconds)
            
            await user.timeout(timeout_until, reason=f"By {interaction.user}: {reason}")
            
            # Log to database
            await self.bot.db.add_moderation_log(
                interaction.guild.id,
                interaction.user.id,
                user.id,
                'timeout',
                reason,
                duration
            )
            
            await interaction.response.send_message(
                f"⏰ {user.mention} has been timed out for {duration}. Reason: {reason}"
            )
            
        except ValueError:
            await interaction.response.send_message("Invalid duration format! Use: 60s, 5m, 1h, 1d")
        except Exception as e:
            await interaction.response.send_message(f"Failed to timeout user: {e}")
    
    @app_commands.command(name="warn", description="Warn a user")
    @app_commands.describe(user="User to warn", reason="Reason for warning")
    @app_commands.default_permissions(moderate_members=True)
    async def warn(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
        """Warn command"""
        if user.top_role >= interaction.user.top_role:
            await interaction.response.send_message("You cannot warn someone with equal or higher role!", ephemeral=True)
            return
        
        # Add warning to database
        await self.bot.db.execute('''
            INSERT INTO warnings (guild_id, user_id, moderator_id, reason)
            VALUES (?, ?, ?, ?)
        ''', (interaction.guild.id, user.id, interaction.user.id, reason))
        
        # Count warnings
        rows = await self.bot.db.fetchall('''
            SELECT COUNT(*) as count FROM warnings 
            WHERE guild_id = ? AND user_id = ? AND expired = 0
        ''', (interaction.guild.id, user.id))
        
        warning_count = rows[0]['count'] if rows else 0
        
        await interaction.response.send_message(
            f"⚠️ {user.mention} has been warned. Reason: {reason}\n"
            f"Total warnings: {warning_count}"
        )
    
    @app_commands.command(name="clear", description="Clear messages from a channel")
    @app_commands.describe(amount="Number of messages to clear (1-100)")
    @app_commands.default_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, amount: int = 10):
        """Clear messages command"""
        if amount < 1 or amount > 100:
            await interaction.response.send_message("Amount must be between 1 and 100", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            deleted = await interaction.channel.purge(limit=amount)
            await interaction.followup.send(f"🧹 Deleted {len(deleted)} messages", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Failed to clear messages: {e}", ephemeral=True)
    
    @app_commands.command(name="mute", description="Voice mute a user")
    @app_commands.describe(user="User to mute", duration="Duration (e.g., 60s, 5m, 1h)", reason="Reason for mute")
    @app_commands.default_permissions(mute_members=True)
    async def mute(self, interaction: discord.Interaction, user: discord.Member, duration: str = "5m", reason: str = "No reason provided"):
        """Voice mute command"""
        if user.top_role >= interaction.user.top_role:
            await interaction.response.send_message("You cannot mute someone with equal or higher role!", ephemeral=True)
            return
        
        if not user.voice:
            await interaction.response.send_message("User is not in a voice channel!")
            return
        
        # Parse duration
        try:
            if duration.endswith('s'):
                seconds = int(duration[:-1])
            elif duration.endswith('m'):
                seconds = int(duration[:-1]) * 60
            elif duration.endswith('h'):
                seconds = int(duration[:-1]) * 3600
            else:
                seconds = int(duration)
            
            await user.edit(mute=True, reason=f"By {interaction.user}: {reason}")
            
            # Log to database
            await self.bot.db.add_moderation_log(
                interaction.guild.id,
                interaction.user.id,
                user.id,
                'voice_mute',
                reason,
                duration
            )
            
            await interaction.response.send_message(
                f"🔇 {user.mention} has been voice muted for {duration}. Reason: {reason}"
            )
            
            # Auto-unmute after duration
            await asyncio.sleep(seconds)
            if user.voice and user.voice.mute:
                await user.edit(mute=False, reason="Auto-unmute after timeout")
                
        except ValueError:
            await interaction.response.send_message("Invalid duration format! Use: 60s, 5m, 1h")
        except Exception as e:
            await interaction.response.send_message(f"Failed to mute user: {e}")

async def setup(bot):
    await bot.add_cog(Moderation(bot))
