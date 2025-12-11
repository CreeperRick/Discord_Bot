import discord
from discord.ext import commands
from discord import app_commands
import platform
from datetime import datetime
import psutil
import time

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()
    
    @app_commands.command(name="ping", description="Check bot latency")
    async def ping(self, interaction: discord.Interaction):
        """Ping command"""
        latency = round(self.bot.latency * 1000)
        
        embed = discord.Embed(
            title="🏓 Pong!",
            color=discord.Color.green()
        )
        embed.add_field(name="Bot Latency", value=f"{latency}ms", inline=True)
        embed.add_field(name="API Latency", value=f"{latency}ms", inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="help", description="Show help menu")
    async def help(self, interaction: discord.Interaction):
        """Help command"""
        embed = discord.Embed(
            title="🤖 Bot Help Menu",
            description="Here are all available commands:",
            color=discord.Color.blue()
        )
        
        # Music commands
        embed.add_field(
            name="🎵 Music Commands",
            value="• `/play [song]` - Play a song\n"
                  "• `/pause` - Pause music\n"
                  "• `/resume` - Resume music\n"
                  "• `/skip` - Skip current song\n"
                  "• `/queue` - Show queue\n"
                  "• `/volume [level]` - Set volume\n"
                  "• `/stop` - Stop music",
            inline=False
        )
        
        # Moderation commands
        embed.add_field(
            name="🛡️ Moderation",
            value="• `/ban [user] [reason]`\n"
                  "• `/kick [user] [reason]`\n"
                  "• `/timeout [user] [duration] [reason]`\n"
                  "• `/warn [user] [reason]`\n"
                  "• `/clear [amount]`\n"
                  "• `/mute [user] [duration] [reason]`",
            inline=False
        )
        
        # Ticket commands
        embed.add_field(
            name="🎫 Tickets",
            value="• `/ticket create [topic]`\n"
                  "• `/ticket close [reason]`\n"
                  "• `/ticket add [user]`\n"
                  "• `/ticket remove [user]`",
            inline=False
        )
        
        # Community commands
        embed.add_field(
            name="🌟 Community",
            value="• `/poll [question] [options...]`\n"
                  "• `/giveaway [prize] [duration] [winners]`\n"
                  "• `/suggest [suggestion]`\n"
                  "• `/rank`\n"
                  "• `/leaderboard`",
            inline=False
        )
        
        # Troll commands
        embed.add_field(
            name="😄 Fun/Troll",
            value="• `/mock [user]`\n"
                  "• `/reverse [text]`\n"
                  "• `/emojify [text]`\n"
                  "• `/rate [thing]`\n"
                  "• `/8ball [question]`\n"
                  "• `/roll [dice]`\n"
                  "• `/coinflip`\n"
                  "• `/choose [options]`",
            inline=False
        )
        
        # Utility commands
        embed.add_field(
            name="🔧 Utility",
            value="• `/ping`\n"
                  "• `/help`\n"
                  "• `/userinfo [user]`\n"
                  "• `/serverinfo`\n"
                  "• `/avatar [user]`\n"
                  "• `/invite`",
            inline=False
        )
        
        embed.set_footer(text="Use / before each command")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="userinfo", description="Get user information")
    async def userinfo(self, interaction: discord.Interaction, user: discord.Member = None):
        """User info command"""
        target = user or interaction.user
        
        embed = discord.Embed(
            title=f"👤 {target.name}'s Info",
            color=target.color
        )
        
        embed.set_thumbnail(url=target.avatar.url)
        
        # Basic info
        embed.add_field(name="Username", value=f"{target.name}#{target.discriminator}", inline=True)
        embed.add_field(name="ID", value=target.id, inline=True)
        embed.add_field(name="Bot", value="Yes" if target.bot else "No", inline=True)
        
        # Dates
        embed.add_field(name="Created", value=f"<t:{int(target.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="Joined", value=f"<t:{int(target.joined_at.timestamp())}:R>", inline=True)
        
        # Roles
        roles = [role.mention for role in target.roles[1:]]  # Skip @everyone
        if roles:
            roles_text = " ".join(roles[:5])
            if len(roles) > 5:
                roles_text += f" (+{len(roles)-5} more)"
        else:
            roles_text = "No roles"
        
        embed.add_field(name=f"Roles ({len(roles)})", value=roles_text, inline=False)
        
        # Status
        status_emojis = {
            "online": "🟢",
            "idle": "🟡",
            "dnd": "🔴",
            "offline": "⚫"
        }
        
        status = str(target.status)
        embed.add_field(name="Status", value=f"{status_emojis.get(status, '❓')} {status.title()}", inline=True)
        
        # Activities
        if target.activity:
            activity_type = str(target.activity.type).split(".")[-1].title()
            embed.add_field(name="Activity", value=f"{activity_type}: {target.activity.name}", inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="serverinfo", description="Get server information")
    async def serverinfo(self, interaction: discord.Interaction):
        """Server info command"""
        guild = interaction.guild
        
        embed = discord.Embed(
            title=f"🏰 {guild.name}",
            color=discord.Color.blue()
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        # Server info
        embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
        embed.add_field(name="ID", value=guild.id, inline=True)
        embed.add_field(name="Created", value=f"<t:{int(guild.created_at.timestamp())}:R>", inline=True)
        
        # Counts
        embed.add_field(name="Members", value=guild.member_count, inline=True)
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="Channels", value=len(guild.channels), inline=True)
        
        # More details
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        
        embed.add_field(
            name="Channel Breakdown",
            value=f"💬 Text: {text_channels}\n"
                  f"🎤 Voice: {voice_channels}\n"
                  f"📁 Categories: {categories}",
            inline=True
        )
        
        # Boosts
        if guild.premium_subscription_count:
            embed.add_field(
                name="Boosts",
                value=f"Level {guild.premium_tier}\n"
                      f"{guild.premium_subscription_count} boosts",
                inline=True
            )
        
        # Features
        if guild.features:
            features = ", ".join(guild.features[:5])
            if len(guild.features) > 5:
                features += "..."
            embed.add_field(name="Features", value=features, inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="avatar", description="Get user's avatar")
    async def avatar(self, interaction: discord.Interaction, user: discord.Member = None):
        """Avatar command"""
        target = user or interaction.user
        
        embed = discord.Embed(
            title=f"{target.name}'s Avatar",
            color=target.color
        )
        
        embed.set_image(url=target.avatar.url)
        
        # Add download links for different formats
        formats = ["png", "jpg", "webp"]
        if target.avatar.is_animated():
            formats.append("gif")
        
        links = " | ".join(
            f"[{fmt.upper()}]({target.avatar.replace(format=fmt, size=4096).url})"
            for fmt in formats
        )
        
        embed.add_field(name="Download", value=links, inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="invite", description="Get bot invite link")
    async def invite(self, interaction: discord.Interaction):
        """Invite command"""
        # Create invite link with recommended permissions
        permissions = discord.Permissions()
        permissions.value = 8  # Administrator for simplicity
        
        embed = discord.Embed(
            title="🤖 Invite Me!",
            description=f"[Click here to invite me to your server!](https://discord.com/oauth2/authorize?client_id={self.bot.user.id}&permissions=8&scope=bot%20applications.commands)",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="Required Permissions",
            value="• Send Messages\n"
                  "• Manage Messages\n"
                  "• Connect to Voice\n"
                  "• Speak in Voice\n"
                  "• Use Slash Commands",
            inline=False
        )
        
        embed.set_footer(text="Thank you for using our bot! ❤️")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="botinfo", description="Get bot information")
    async def botinfo(self, interaction: discord.Interaction):
        """Bot info command"""
        # Calculate uptime
        uptime_seconds = int(time.time() - self.start_time)
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        uptime_str = ""
        if days: uptime_str += f"{days}d "
        if hours: uptime_str += f"{hours}h "
        if minutes: uptime_str += f"{minutes}m "
        uptime_str += f"{seconds}s"
        
        # Get system info
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used = memory.used / (1024 ** 3)  # Convert to GB
        memory_total = memory.total / (1024 ** 3)  # Convert to GB
        
        embed = discord.Embed(
            title="🤖 Bot Information",
            color=discord.Color.blurple()
        )
        
        # Bot info
        embed.add_field(name="Bot Name", value=self.bot.user.name, inline=True)
        embed.add_field(name="Bot ID", value=self.bot.user.id, inline=True)
        embed.add_field(name="Discord.py Version", value=discord.__version__, inline=True)
        
        # Stats
        embed.add_field(name="Servers", value=len(self.bot.guilds), inline=True)
        embed.add_field(name="Users", value=sum(g.member_count for g in self.bot.guilds), inline=True)
        embed.add_field(name="Commands", value=len(self.bot.tree.get_commands()), inline=True)
        
        # System
        embed.add_field(name="Uptime", value=uptime_str, inline=True)
        embed.add_field(name="CPU Usage", value=f"{cpu_percent}%", inline=True)
        embed.add_field(name="Memory", value=f"{memory_percent}% ({memory_used:.1f}/{memory_total:.1f} GB)", inline=True)
        
        # Python info
        embed.add_field(name="Python Version", value=platform.python_version(), inline=True)
        embed.add_field(name="Platform", value=platform.system(), inline=True)
        
        embed.set_footer(text=f"Made with ❤️ using discord.py")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Utility(bot))
