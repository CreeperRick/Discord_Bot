import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio
from collections import deque
import json

# Suppress yt-dlp warnings
yt_dlp.utils.bug_reports_message = lambda: ''

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}
        self.now_playing = {}
        self.voice_clients = {}
        
        # YT-DLP options
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
            'restrictfilenames': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'ytsearch',
            'source_address': '0.0.0.0',
            'extract_flat': False,
        }
        
        self.ffmpeg_options = {
            'options': '-vn',
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
        }
    
    @app_commands.command(name="play", description="Play a song from YouTube")
    @app_commands.describe(query="Song name or YouTube URL")
    async def play(self, interaction: discord.Interaction, query: str):
        """Play music command"""
        await interaction.response.defer()
        
        if not interaction.user.voice:
            await interaction.followup.send("You need to be in a voice channel!")
            return
        
        voice_channel = interaction.user.voice.channel
        
        # Connect to voice channel
        if interaction.guild.id not in self.voice_clients:
            try:
                vc = await voice_channel.connect()
                self.voice_clients[interaction.guild.id] = vc
            except Exception as e:
                await interaction.followup.send(f"Failed to connect: {e}")
                return
        else:
            vc = self.voice_clients[interaction.guild.id]
        
        # Get song info
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(query, download=False)
                
                if 'entries' in info:
                    info = info['entries'][0]
                
                song = {
                    'title': info.get('title', 'Unknown Title'),
                    'url': info.get('webpage_url', query),
                    'audio_url': info.get('url'),
                    'duration': info.get('duration', 0),
                    'requester': interaction.user.name,
                    'thumbnail': info.get('thumbnail')
                }
                
                # Add to queue
                if interaction.guild.id not in self.queues:
                    self.queues[interaction.guild.id] = deque()
                
                self.queues[interaction.guild.id].append(song)
                
                # Start playing if not already
                if not vc.is_playing():
                    await self.play_next(interaction.guild.id)
                    await interaction.followup.send(f"🎵 Now playing: **{song['title']}**")
                else:
                    await interaction.followup.send(f"✅ Added to queue: **{song['title']}**")
                    
        except Exception as e:
            await interaction.followup.send(f"Error: {str(e)}")
    
    async def play_next(self, guild_id):
        """Play next song in queue"""
        if guild_id not in self.queues or not self.queues[guild_id]:
            return
        
        if guild_id not in self.voice_clients:
            return
        
        vc = self.voice_clients[guild_id]
        song = self.queues[guild_id].popleft()
        self.now_playing[guild_id] = song
        
        try:
            # Play audio
            source = await discord.FFmpegOpusAudio.from_probe(
                song['audio_url'],
                **self.ffmpeg_options
            )
            
            vc.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(
                self.play_next(guild_id), self.bot.loop
            ))
            
        except Exception as e:
            print(f"Error playing audio: {e}")
            await self.play_next(guild_id)
    
    @app_commands.command(name="pause", description="Pause the current song")
    async def pause(self, interaction: discord.Interaction):
        """Pause command"""
        if interaction.guild.id in self.voice_clients:
            vc = self.voice_clients[interaction.guild.id]
            if vc.is_playing():
                vc.pause()
                await interaction.response.send_message("⏸️ Music paused")
            else:
                await interaction.response.send_message("No music is playing")
        else:
            await interaction.response.send_message("Not connected to voice channel")
    
    @app_commands.command(name="resume", description="Resume paused music")
    async def resume(self, interaction: discord.Interaction):
        """Resume command"""
        if interaction.guild.id in self.voice_clients:
            vc = self.voice_clients[interaction.guild.id]
            if vc.is_paused():
                vc.resume()
                await interaction.response.send_message("▶️ Music resumed")
            else:
                await interaction.response.send_message("Music is not paused")
        else:
            await interaction.response.send_message("Not connected to voice channel")
    
    @app_commands.command(name="skip", description="Skip the current song")
    async def skip(self, interaction: discord.Interaction):
        """Skip command"""
        if interaction.guild.id in self.voice_clients:
            vc = self.voice_clients[interaction.guild.id]
            if vc.is_playing():
                vc.stop()
                await interaction.response.send_message("⏭️ Skipped current song")
            else:
                await interaction.response.send_message("No music is playing")
        else:
            await interaction.response.send_message("Not connected to voice channel")
    
    @app_commands.command(name="queue", description="Show the current music queue")
    async def queue(self, interaction: discord.Interaction):
        """Queue command"""
        if interaction.guild.id not in self.queues or not self.queues[interaction.guild.id]:
            await interaction.response.send_message("Queue is empty")
            return
        
        queue_list = self.queues[interaction.guild.id]
        message = "**Music Queue:**\n"
        
        for i, song in enumerate(queue_list, 1):
            message += f"{i}. {song['title']} (Requested by: {song['requester']})\n"
        
        await interaction.response.send_message(message[:1900])
    
    @app_commands.command(name="volume", description="Set the volume (1-100)")
    @app_commands.describe(level="Volume level (1-100)")
    async def volume(self, interaction: discord.Interaction, level: int):
        """Volume command"""
        if not 1 <= level <= 100:
            await interaction.response.send_message("Volume must be between 1 and 100")
            return
        
        if interaction.guild.id in self.voice_clients:
            vc = self.voice_clients[interaction.guild.id]
            vc.source.volume = level / 100
            await interaction.response.send_message(f"🔊 Volume set to {level}%")
        else:
            await interaction.response.send_message("Not connected to voice channel")
    
    @app_commands.command(name="stop", description="Stop music and clear queue")
    async def stop(self, interaction: discord.Interaction):
        """Stop command"""
        if interaction.guild.id in self.voice_clients:
            vc = self.voice_clients[interaction.guild.id]
            
            # Clear queue
            if interaction.guild.id in self.queues:
                self.queues[interaction.guild.id].clear()
            
            # Stop playing
            vc.stop()
            
            # Disconnect
            await vc.disconnect()
            del self.voice_clients[interaction.guild.id]
            
            await interaction.response.send_message("⏹️ Music stopped and queue cleared")
        else:
            await interaction.response.send_message("Not connected to voice channel")
    
    # Web control method
    async def web_control(self, guild_id, action, data):
        """Control music from web dashboard"""
        if guild_id not in self.voice_clients:
            return False
        
        vc = self.voice_clients[guild_id]
        
        if action == 'pause':
            if vc.is_playing():
                vc.pause()
                return True
        elif action == 'resume':
            if vc.is_paused():
                vc.resume()
                return True
        elif action == 'skip':
            if vc.is_playing():
                vc.stop()
                return True
        elif action == 'stop':
            vc.stop()
            if guild_id in self.voice_clients:
                await vc.disconnect()
                del self.voice_clients[guild_id]
            return True
        
        return False
    
    def get_guild_status(self, guild_id):
        """Get music status for a guild"""
        status = {
            'guild_id': guild_id,
            'is_playing': False,
            'is_paused': False,
            'now_playing': None,
            'queue_length': 0
        }
        
        if guild_id in self.voice_clients:
            vc = self.voice_clients[guild_id]
            status['is_playing'] = vc.is_playing()
            status['is_paused'] = vc.is_paused()
            
        if guild_id in self.now_playing:
            status['now_playing'] = self.now_playing[guild_id]
        
        if guild_id in self.queues:
            status['queue_length'] = len(self.queues[guild_id])
        
        return status

async def setup(bot):
    await bot.add_cog(Music(bot))
