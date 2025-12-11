import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime, timedelta
import random

class PollView(View):
    def __init__(self, poll_id, options):
        super().__init__(timeout=None)
        self.poll_id = poll_id
        for i, option in enumerate(options):
            button = Button(label=option[:20], style=discord.ButtonStyle.secondary, custom_id=f"poll_{poll_id}_{i}")
            button.callback = self.vote_callback
            self.add_item(button)
    
    async def vote_callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("Thanks for voting!", ephemeral=True)

class GiveawayView(View):
    def __init__(self, giveaway_id):
        super().__init__(timeout=None)
        self.giveaway_id = giveaway_id
        button = Button(label="Enter Giveaway", style=discord.ButtonStyle.success, custom_id=f"giveaway_{giveaway_id}")
        button.callback = self.enter_callback
        self.add_item(button)
    
    async def enter_callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("You've entered the giveaway!", ephemeral=True)

class Community(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_polls = {}
        self.active_giveaways = {}
    
    @app_commands.command(name="poll", description="Create a poll")
    @app_commands.describe(question="Poll question", option1="Option 1", option2="Option 2", 
                          option3="Option 3", option4="Option 4", option5="Option 5")
    async def poll(self, interaction: discord.Interaction, question: str, option1: str, option2: str,
                  option3: str = None, option4: str = None, option5: str = None):
        """Create a poll"""
        options = [option1, option2]
        if option3: options.append(option3)
        if option4: options.append(option4)
        if option5: options.append(option5)
        
        # Store poll in database
        options_json = json.dumps(options)
        
        # Create embed
        embed = discord.Embed(
            title=f"📊 Poll: {question}",
            color=discord.Color.purple(),
            timestamp=datetime.utcnow()
        )
        
        for i, option in enumerate(options, 1):
            embed.add_field(name=f"Option {i}", value=option, inline=False)
        
        embed.set_footer(text=f"Poll created by {interaction.user}")
        
        # Send poll with buttons
        view = PollView(f"{interaction.message.id}", options)
        await interaction.response.send_message(embed=embed, view=view)
    
    @app_commands.command(name="giveaway", description="Start a giveaway")
    @app_commands.describe(prize="Giveaway prize", duration="Duration (e.g., 1h, 1d, 7d)", winners="Number of winners")
    @app_commands.default_permissions(manage_guild=True)
    async def giveaway(self, interaction: discord.Interaction, prize: str, duration: str, winners: int = 1):
        """Start a giveaway"""
        # Parse duration
        try:
            if duration.endswith('m'):
                seconds = int(duration[:-1]) * 60
            elif duration.endswith('h'):
                seconds = int(duration[:-1]) * 3600
            elif duration.endswith('d'):
                seconds = int(duration[:-1]) * 86400
            else:
                seconds = int(duration)
            
            ends_at = datetime.utcnow() + timedelta(seconds=seconds)
            
            # Create embed
            embed = discord.Embed(
                title="🎉 Giveaway!",
                description=f"**Prize:** {prize}\n**Winners:** {winners}\n**Ends:** <t:{int(ends_at.timestamp())}:R>",
                color=discord.Color.gold(),
                timestamp=ends_at
            )
            embed.set_footer(text=f"Hosted by {interaction.user}")
            
            # Store in database
            await self.bot.db.execute('''
                INSERT INTO giveaways (guild_id, channel_id, prize, winners, ends_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (interaction.guild.id, interaction.channel.id, prize, winners, ends_at.isoformat()))
            
            # Send giveaway
            view = GiveawayView(f"{interaction.message.id}")
            message = await interaction.response.send_message(embed=embed, view=view)
            
            # Schedule ending
            asyncio.create_task(self.end_giveaway(interaction.guild.id, interaction.channel.id, message.id, ends_at, winners))
            
        except ValueError:
            await interaction.response.send_message("Invalid duration! Use: 1h, 1d, 7d")
    
    async def end_giveaway(self, guild_id, channel_id, message_id, ends_at, winners):
        """End a giveaway"""
        await asyncio.sleep((ends_at - datetime.utcnow()).total_seconds())
        
        # Get entries from database
        entries = []  # This would come from your database
        
        if entries:
            winners_list = random.sample(entries, min(winners, len(entries)))
            winners_mentions = ", ".join(f"<@{w}>" for w in winners_list)
            
            # Update message
            channel = self.bot.get_channel(channel_id)
            if channel:
                try:
                    message = await channel.fetch_message(message_id)
                    embed = message.embeds[0]
                    embed.description += f"\n\n**🎊 Winners:** {winners_mentions}"
                    embed.color = discord.Color.green()
                    await message.edit(embed=embed, view=None)
                except:
                    pass
    
    @app_commands.command(name="suggest", description="Submit a suggestion")
    @app_commands.describe(suggestion="Your suggestion")
    async def suggest(self, interaction: discord.Interaction, suggestion: str):
        """Submit a suggestion"""
        # Get suggestion channel from settings
        settings = await self.bot.db.get_guild_settings(interaction.guild.id)
        suggestion_channel_id = settings.get('suggestion_channel_id') if settings else None
        
        if suggestion_channel_id:
            channel = self.bot.get_channel(suggestion_channel_id)
            if channel:
                embed = discord.Embed(
                    title="💡 New Suggestion",
                    description=suggestion,
                    color=discord.Color.blue(),
                    timestamp=datetime.utcnow()
                )
                embed.set_footer(text=f"Suggested by {interaction.user}", icon_url=interaction.user.avatar.url)
                
                message = await channel.send(embed=embed)
                await message.add_reaction("✅")
                await message.add_reaction("❌")
                
                await interaction.response.send_message("✅ Suggestion submitted!", ephemeral=True)
                return
        
        await interaction.response.send_message("✅ Suggestion received! (No suggestion channel configured)", ephemeral=True)
    
    @app_commands.command(name="rank", description="Check your level and rank")
    async def rank(self, interaction: discord.Interaction, user: discord.Member = None):
        """Check rank"""
        target = user or interaction.user
        
        # Get user data from database
        row = await self.bot.db.fetchone('''
            SELECT xp, level FROM users 
            WHERE guild_id = ? AND user_id = ?
        ''', (interaction.guild.id, target.id))
        
        if row:
            xp, level = row['xp'], row['level']
        else:
            xp, level = 0, 1
        
        # Create embed
        embed = discord.Embed(
            title=f"🏆 {target.name}'s Rank",
            color=discord.Color.blurple()
        )
        embed.add_field(name="Level", value=str(level), inline=True)
        embed.add_field(name="XP", value=str(xp), inline=True)
        embed.add_field(name="Next Level", value=f"{1000 - (xp % 1000)} XP", inline=True)
        embed.set_thumbnail(url=target.avatar.url)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="leaderboard", description="Server XP leaderboard")
    async def leaderboard(self, interaction: discord.Interaction):
        """Show leaderboard"""
        # Get top 10 users
        rows = await self.bot.db.fetchall('''
            SELECT user_id, xp, level FROM users 
            WHERE guild_id = ? 
            ORDER BY xp DESC 
            LIMIT 10
        ''', (interaction.guild.id,))
        
        if not rows:
            await interaction.response.send_message("No users on leaderboard yet!")
            return
        
        embed = discord.Embed(
            title="🏆 Server Leaderboard",
            color=discord.Color.gold()
        )
        
        for i, row in enumerate(rows, 1):
            user = interaction.guild.get_member(row['user_id'])
            username = user.name if user else f"User {row['user_id']}"
            embed.add_field(
                name=f"{i}. {username}",
                value=f"Level {row['level']} • {row['xp']} XP",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Community(bot))
