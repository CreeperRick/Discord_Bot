import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
from datetime import datetime

class Troll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger
        
    @app_commands.command(name="mock", description="Mock a user (fun, not harmful)")
    @app_commands.describe(user="User to mock", message="Custom message (optional)")
    async def mock(self, interaction: discord.Interaction, user: discord.Member, message: str = None):
        """Mock a user in a fun way"""
        if user == interaction.user:
            await interaction.response.send_message("You can't mock yourself! 😜", ephemeral=True)
            return
        
        if not message:
            # Get recent message from user
            try:
                messages = [msg async for msg in interaction.channel.history(limit=10)]
                user_messages = [msg for msg in messages if msg.author == user]
                if user_messages:
                    message = user_messages[0].content
                else:
                    message = "I have nothing to say!"
            except:
                message = "Something funny!"
        
        # Create mocking text
        mocked = ""
        for i, char in enumerate(message):
            if i % 2 == 0:
                mocked += char.upper()
            else:
                mocked += char.lower()
        
        embed = discord.Embed(
            title=f"😂 Mocking {user.name}",
            description=mocked,
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=f"Mocked by {interaction.user}", icon_url=interaction.user.avatar.url)
        
        await interaction.response.send_message(embed=embed)
        self.logger.info(f"{interaction.user} mocked {user} in {interaction.guild.name}")
    
    @app_commands.command(name="reverse", description="Reverse text")
    @app_commands.describe(text="Text to reverse")
    async def reverse(self, interaction: discord.Interaction, text: str):
        """Reverse text command"""
        reversed_text = text[::-1]
        
        embed = discord.Embed(
            title="🔀 Reversed Text",
            description=reversed_text,
            color=discord.Color.blue()
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="emojify", description="Convert text to emojis")
    @app_commands.describe(text="Text to emojify")
    async def emojify(self, interaction: discord.Interaction, text: str):
        """Convert text to regional indicator emojis"""
        emoji_map = {
            'a': '🇦', 'b': '🇧', 'c': '🇨', 'd': '🇩', 'e': '🇪',
            'f': '🇫', 'g': '🇬', 'h': '🇭', 'i': '🇮', 'j': '🇯',
            'k': '🇰', 'l': '🇱', 'm': '🇲', 'n': '🇳', 'o': '🇴',
            'p': '🇵', 'q': '🇶', 'r': '🇷', 's': '🇸', 't': '🇹',
            'u': '🇺', 'v': '🇻', 'w': '🇼', 'x': '🇽', 'y': '🇾',
            'z': '🇿', '0': '0️⃣', '1': '1️⃣', '2': '2️⃣', '3': '3️⃣',
            '4': '4️⃣', '5': '5️⃣', '6': '6️⃣', '7': '7️⃣', '8': '8️⃣',
            '9': '9️⃣', ' ': '   ', '!': '❗', '?': '❓'
        }
        
        emojified = ""
        for char in text.lower():
            if char in emoji_map:
                emojified += emoji_map[char] + " "
            else:
                emojified += char + " "
        
        await interaction.response.send_message(emojified[:1900])
    
    @app_commands.command(name="rate", description="Rate something 0-10")
    @app_commands.describe(thing="Thing to rate")
    async def rate(self, interaction: discord.Interaction, thing: str):
        """Rate something randomly"""
        rating = random.randint(0, 10)
        
        # Create rating bar
        filled = "⭐" * rating
        empty = "☆" * (10 - rating)
        
        embed = discord.Embed(
            title="⭐ Rating",
            description=f"I rate **{thing}** a **{rating}/10**",
            color=discord.Color.gold()
        )
        embed.add_field(name="Rating", value=f"{filled}{empty}", inline=False)
        
        # Add funny comments
        comments = [
            "Wow, that's impressive!",
            "Could be better...",
            "Absolutely amazing!",
            "Meh, it's okay.",
            "Perfection!",
            "Not my cup of tea.",
            "Absolutely terrible!",
            "Pretty decent!",
            "Needs improvement.",
            "Top tier!",
            "I've seen better."
        ]
        
        embed.add_field(name="Comment", value=random.choice(comments), inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="8ball", description="Ask the magic 8-ball a question")
    @app_commands.describe(question="Your question for the 8-ball")
    async def eight_ball(self, interaction: discord.Interaction, question: str):
        """Magic 8-ball command"""
        responses = [
            "It is certain.", "It is decidedly so.", "Without a doubt.",
            "Yes definitely.", "You may rely on it.", "As I see it, yes.",
            "Most likely.", "Outlook good.", "Yes.", "Signs point to yes.",
            "Reply hazy, try again.", "Ask again later.", "Better not tell you now.",
            "Cannot predict now.", "Concentrate and ask again.", "Don't count on it.",
            "My reply is no.", "My sources say no.", "Outlook not so good.",
            "Very doubtful."
        ]
        
        embed = discord.Embed(
            title="🎱 Magic 8-Ball",
            color=discord.Color.dark_grey()
        )
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Answer", value=random.choice(responses), inline=False)
        embed.set_footer(text="The magic 8-ball has spoken!")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="roll", description="Roll dice")
    @app_commands.describe(dice="Dice to roll (e.g., 2d6)")
    async def roll(self, interaction: discord.Interaction, dice: str = "1d6"):
        """Roll dice command"""
        try:
            if "d" not in dice:
                await interaction.response.send_message("Format: NdM (e.g., 2d6 for two six-sided dice)")
                return
            
            num, sides = dice.split("d")
            num = int(num)
            sides = int(sides)
            
            if num > 20:
                await interaction.response.send_message("Maximum 20 dice at once!", ephemeral=True)
                return
            
            if sides > 100:
                await interaction.response.send_message("Maximum 100 sides per die!", ephemeral=True)
                return
            
            rolls = [random.randint(1, sides) for _ in range(num)]
            total = sum(rolls)
            
            embed = discord.Embed(
                title="🎲 Dice Roll",
                color=discord.Color.green()
            )
            embed.add_field(name="Roll", value=dice, inline=True)
            embed.add_field(name="Results", value=", ".join(map(str, rolls)), inline=True)
            embed.add_field(name="Total", value=str(total), inline=True)
            
            # Add fun comment
            if total == num * sides:
                embed.description = "🎉 **NATURAL MAX!** 🎉"
                embed.color = discord.Color.gold()
            elif total == num:
                embed.description = "😬 **NATURAL MIN!** 😬"
                embed.color = discord.Color.red()
            
            await interaction.response.send_message(embed=embed)
            
        except ValueError:
            await interaction.response.send_message("Invalid format! Use: NdM (e.g., 2d6)", ephemeral=True)
    
    @app_commands.command(name="coinflip", description="Flip a coin")
    async def coinflip(self, interaction: discord.Interaction):
        """Flip a coin"""
        result = random.choice(["Heads", "Tails"])
        
        embed = discord.Embed(
            title="🪙 Coin Flip",
            description=f"The coin landed on... **{result}**!",
            color=discord.Color.light_grey()
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="choose", description="Choose between options")
    @app_commands.describe(options="Options separated by | (e.g., pizza|burger|taco)")
    async def choose(self, interaction: discord.Interaction, options: str):
        """Choose between options"""
        choices = [opt.strip() for opt in options.split("|") if opt.strip()]
        
        if len(choices) < 2:
            await interaction.response.send_message("Provide at least 2 options separated by |", ephemeral=True)
            return
        
        if len(choices) > 10:
            await interaction.response.send_message("Maximum 10 options!", ephemeral=True)
            return
        
        chosen = random.choice(choices)
        
        embed = discord.Embed(
            title="🤔 I Choose...",
            description=f"**{chosen}**",
            color=discord.Color.purple()
        )
        embed.add_field(name="Options", value="\n".join(choices), inline=False)
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Troll(bot))
