import discord, asyncio
from discord.ext import commands
from discord import app_commands
from yt_dlp import YoutubeDL

YTDL_OPTS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
}
FFMPEG_OPTIONS = {'options': '-vn'}
ytdl = YoutubeDL(YTDL_OPTS)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}

    async def ensure_voice(self, interaction):
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message('You must be in a voice channel.', ephemeral=True)
            return None
        channel = interaction.user.voice.channel
        vc = interaction.guild.voice_client
        if not vc:
            await channel.connect()
            vc = interaction.guild.voice_client
        return vc

    @app_commands.command(name='play', description='Play a YouTube URL or search term')
    async def play(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        vc = await self.ensure_voice(interaction)
        if not vc:
            return
        loop = asyncio.get_event_loop()
        try:
            info = await loop.run_in_executor(None, lambda: ytdl.extract_info(query, download=False))
        except Exception as e:
            await interaction.followup.send(f'Error fetching info: {e}', ephemeral=True); return
        if 'entries' in info:
            info = info['entries'][0]
        stream_url = info.get('url')
        title = info.get('title')
        source = discord.FFmpegPCMAudio(stream_url, **FFMPEG_OPTIONS)
        def after(err):
            if err:
                print('Player error:', err)
            asyncio.run_coroutine_threadsafe(self._play_next(interaction.guild_id), self.bot.loop)
        vc.play(source, after=after)
        await interaction.followup.send(f'Now playing: {title}', ephemeral=False)

    async def _play_next(self, guild_id:int):
        q = self.queues.get(guild_id, [])
        if not q:
            vc = self.bot.get_guild(guild_id).voice_client
            if vc and not vc.is_playing():
                try: await vc.disconnect()
                except: pass
            return
        item = q.pop(0)
        guild = self.bot.get_guild(guild_id)
        vc = guild.voice_client
        if not vc:
            return
        stream_url = item.get('url')
        source = discord.FFmpegPCMAudio(stream_url, **FFMPEG_OPTIONS)
        vc.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(self._play_next(guild_id), self.bot.loop))

    @app_commands.command(name='queue', description='Show queue')
    async def queue_cmd(self, interaction: discord.Interaction):
        q = self.queues.get(interaction.guild.id, [])
        if not q:
            return await interaction.response.send_message('Queue empty.', ephemeral=True)
        lines = [f'{i+1}. {t.get("title","unknown")}' for i,t in enumerate(q[:10])]
        await interaction.response.send_message('\\n'.join(lines), ephemeral=True)

    @app_commands.command(name='stop', description='Stop playback and clear queue')
    @app_commands.checks.has_permissions(manage_guild=True)
    async def stop(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if not vc or not vc.is_connected():
            return await interaction.response.send_message('Not connected.', ephemeral=True)
        vc.stop()
        self.queues[interaction.guild.id] = []
        await interaction.response.send_message('Stopped and cleared queue.', ephemeral=True)

async def setup(bot):
    await bot.add_cog(Music(bot))
