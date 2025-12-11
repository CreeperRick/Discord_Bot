from discord import app_commands, Interaction
from discord.ext import commands, tasks
import discord, time
from utils.db_async import DB

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reminder_task.start()

    @app_commands.command(name='poll', description='Create a quick reaction poll')
    async def poll(self, interaction: Interaction, question: str):
        await interaction.response.send_message('Creating poll...', ephemeral=True)
        m = await interaction.followup.send(f'📊 **Poll:** {question}')
        await m.add_reaction('👍'); await m.add_reaction('👎'); await m.add_reaction('🤷')

    @app_commands.command(name='remindme', description='Set a reminder (seconds)')
    async def remindme(self, interaction: Interaction, seconds: int, content: str):
        ts = int(time.time()) + seconds
        await DB.add_reminder(interaction.guild.id, interaction.user.id, content, ts)
        await interaction.response.send_message(f'Reminder set for {seconds} seconds from now.', ephemeral=True)

    @app_commands.command(name='serverstats', description='Show server stats')
    async def serverstats(self, interaction: Interaction):
        g = interaction.guild
        embed = discord.Embed(title=f'Stats for {g.name}', color=discord.Color.blurple())
        embed.add_field(name='Members', value=str(g.member_count))
        embed.add_field(name='Channels', value=str(len(g.channels)))
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @tasks.loop(seconds=20)
    async def reminder_task(self):
        now = int(time.time())
        rows = await DB.get_due_reminders(now)
        for r in rows:
            rid, guild_id, user_id, content = r
            g = self.bot.get_guild(guild_id)
            if not g:
                await DB.delete_reminder(rid); continue
            member = g.get_member(user_id)
            if member:
                try:
                    await member.send(f'Reminder: {content}')
                except:
                    channel = g.system_channel or next((c for c in g.text_channels if c.permissions_for(g.me).send_messages), None)
                    if channel:
                        await channel.send(f'{member.mention} Reminder: {content}')
            await DB.delete_reminder(rid)

async def setup(bot):
    await bot.add_cog(Utility(bot))
