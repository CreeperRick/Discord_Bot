import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View, Select
import asyncio
from datetime import datetime

class TicketView(View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog
    
    @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.primary, custom_id="create_ticket")
    async def create_ticket(self, interaction: discord.Interaction, button: Button):
        await self.cog.create_ticket_command(interaction)

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ticket_channels = {}
    
    @app_commands.command(name="ticket", description="Ticket system commands")
    @app_commands.describe(action="Action to perform", topic="Ticket topic (for create)", user="User (for add/remove)", reason="Reason (for close)")
    async def ticket(self, interaction: discord.Interaction, action: str, topic: str = None, user: discord.Member = None, reason: str = "No reason provided"):
        """Main ticket command"""
        
        if action == "create":
            await self.create_ticket_command(interaction, topic)
        elif action == "close":
            await self.close_ticket_command(interaction, reason)
        elif action == "add":
            await self.add_user_command(interaction, user)
        elif action == "remove":
            await self.remove_user_command(interaction, user)
        else:
            await interaction.response.send_message("Invalid action! Use: create, close, add, remove")
    
    async def create_ticket_command(self, interaction: discord.Interaction, topic: str = None):
        """Create a ticket"""
        await interaction.response.defer(ephemeral=True)
        
        if not topic:
            topic = "No topic provided"
        
        # Check if user already has open ticket
        existing = await self.bot.db.fetchone('''
            SELECT * FROM tickets 
            WHERE guild_id = ? AND user_id = ? AND status = 'open'
        ''', (interaction.guild.id, interaction.user.id))
        
        if existing:
            await interaction.followup.send("You already have an open ticket!", ephemeral=True)
            return
        
        # Get ticket category
        settings = await self.bot.db.get_guild_settings(interaction.guild.id)
        category_id = settings['ticket_category_id'] if settings else None
        
        category = None
        if category_id:
            category = discord.utils.get(interaction.guild.categories, id=category_id)
        
        if not category:
            # Create category if it doesn't exist
            category = await interaction.guild.create_category("Tickets")
            await self.bot.db.update_guild_settings(interaction.guild.id, ticket_category_id=category.id)
        
        # Create ticket channel
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }
        
        ticket_channel = await category.create_text_channel(
            f"ticket-{interaction.user.name}",
            overwrites=overwrites
        )
        
        # Add to database
        ticket_id = await self.bot.db.create_ticket(
            interaction.guild.id,
            interaction.user.id,
            ticket_channel.id,
            topic
        )
        
        # Store mapping
        self.ticket_channels[ticket_channel.id] = ticket_id
        
        # Send welcome message
        embed = discord.Embed(
            title=f"Ticket #{ticket_id}",
            description=f"**Topic:** {topic}\n\nPlease describe your issue in detail. Staff will assist you shortly.",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Created by {interaction.user}", icon_url=interaction.user.avatar.url)
        embed.timestamp = datetime.utcnow()
        
        # Add close button
        close_button = Button(label="Close Ticket", style=discord.ButtonStyle.danger, custom_id=f"close_{ticket_id}")
        
        async def close_callback(interaction: discord.Interaction):
            await self.close_ticket(interaction, ticket_id, "Closed via button")
        
        close_button.callback = close_callback
        
        view = View()
        view.add_item(close_button)
        
        await ticket_channel.send(embed=embed, view=view)
        await interaction.followup.send(f"✅ Ticket created: {ticket_channel.mention}", ephemeral=True)
    
    async def close_ticket_command(self, interaction: discord.Interaction, reason: str):
        """Close a ticket"""
        # Check if this is a ticket channel
        if interaction.channel.id not in self.ticket_channels:
            await interaction.response.send_message("This is not a ticket channel!", ephemeral=True)
            return
        
        ticket_id = self.ticket_channels[interaction.channel.id]
        await self.close_ticket(interaction, ticket_id, reason)
    
    async def close_ticket(self, interaction: discord.Interaction, ticket_id: int, reason: str):
        """Close ticket helper"""
        await interaction.response.defer()
        
        # Update database
        await self.bot.db.execute('''
            UPDATE tickets 
            SET status = 'closed', closed_at = CURRENT_TIMESTAMP, 
                closed_by = ?, closed_reason = ?
            WHERE ticket_id = ?
        ''', (interaction.user.id, reason, ticket_id))
        
        # Send closing message
        embed = discord.Embed(
            title=f"Ticket #{ticket_id} Closed",
            description=f"**Reason:** {reason}\n\nThis ticket has been closed by {interaction.user.mention}.",
            color=discord.Color.red()
        )
        embed.set_footer(text=f"Closed by {interaction.user}", icon_url=interaction.user.avatar.url)
        embed.timestamp = datetime.utcnow()
        
        await interaction.channel.send(embed=embed)
        
        # Delete channel after delay
        await asyncio.sleep(10)
        try:
            await interaction.channel.delete()
        except:
            pass
        
        # Remove from mapping
        if interaction.channel.id in self.ticket_channels:
            del self.ticket_channels[interaction.channel.id]
    
    async def add_user_command(self, interaction: discord.Interaction, user: discord.Member):
        """Add user to ticket"""
        if interaction.channel.id not in self.ticket_channels:
            await interaction.response.send_message("This is not a ticket channel!", ephemeral=True)
            return
        
        # Add permissions
        await interaction.channel.set_permissions(user, read_messages=True, send_messages=True)
        await interaction.response.send_message(f"✅ Added {user.mention} to the ticket")
    
    async def remove_user_command(self, interaction: discord.Interaction, user: discord.Member):
        """Remove user from ticket"""
        if interaction.channel.id not in self.ticket_channels:
            await interaction.response.send_message("This is not a ticket channel!", ephemeral=True)
            return
        
        # Remove permissions
        await interaction.channel.set_permissions(user, overwrite=None)
        await interaction.response.send_message(f"✅ Removed {user.mention} from the ticket")
    
    @app_commands.command(name="ticketsetup", description="Setup ticket system")
    @app_commands.default_permissions(administrator=True)
    async def ticket_setup(self, interaction: discord.Interaction):
        """Setup ticket system"""
        embed = discord.Embed(
            title="Support Tickets",
            description="Click the button below to create a support ticket.\n\n"
                       "Our staff team will assist you as soon as possible.",
            color=discord.Color.green()
        )
        
        view = TicketView(self)
        await interaction.response.send_message(embed=embed, view=view)
    
    # Web dashboard methods
    async def web_action(self, action, ticket_id, data):
        """Handle web dashboard actions"""
        if action == 'close':
            # Close ticket from web
            await self.bot.db.execute('''
                UPDATE tickets 
                SET status = 'closed', closed_at = CURRENT_TIMESTAMP, 
                    closed_by = 0, closed_reason = ?
                WHERE ticket_id = ?
            ''', (data.get('reason', 'Closed via web'), ticket_id))
            return {'success': True}
        
        return {'success': False}

async def setup(bot):
    await bot.add_cog(Tickets(bot))
