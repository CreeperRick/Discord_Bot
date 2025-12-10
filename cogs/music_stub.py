# cogs/music_stub.py
import discord
from discord.ext import commands
from typing import Dict, List, Optional

class MusicCog(commands.Cog):
    """Music skeleton. Requires ffmpeg + PyNaCl to actually play audio.
    This cog provides join/leave and an in-memory queue. To enable playing,
    implement `play_next` to create a discord.FFmpegPCMAudio source using yt-dlp.
    """

    def __init__(self, bot):
        self.bot = bot
        self.queues: Dict[int, List[dict]] = {}  # guild_id -> list of tracks

    @commands.command(name="join")
    async def join(self, ctx):
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send("You must be in a voice channel.")
        vc = ctx.voice_client
        channel = ctx.author.voice.channel
        if vc and vc.channel.id == channel.id:
            return await ctx.send("Already connected.")
        if vc:
            await vc.move_to(channel)
            return await ctx.send(f"Moved to {channel.name}")
        await channel.connect()
        await ctx.send(f"Connected to {channel.name}")

    @commands.command(name="leave")
    async def leave(self, ctx):
        vc = ctx.voice_client
        if not vc:
            return await ctx.send("Not connected.")
        await vc.disconnect()
        await ctx.send("Disconnected.")

    @commands.command(name="queue")
    async def queue(self, ctx):
        q = self.queues.get(ctx.guild.id, [])
        if not q:
            return await ctx.send("Queue is empty.")
        lines = [f"{i+1}. {t.get('title','unknown')}" for i,t in enumerate(q[:10])]
        await ctx.send("\n".join(lines))

    @commands.command(name="add")
    async def add(self, ctx, *, query: str):
        # This simply appends a query item to the queue. Integration with yt-dlp needed for real streams.
        self.queues.setdefault(ctx.guild.id, []).append({"title": query, "requester": ctx.author.id})
        await ctx.send(f"Added to queue: {query}")

    # placeholder play command — does not stream audio by default
    @commands.command(name="play")
    async def play(self, ctx):
        # Pseudocode: ensure ffmpeg + yt-dlp present; then create a FFmpegPCMAudio source and play
        if not ctx.voice_client:
            await ctx.invoke(self.join)
        await ctx.send("Play command is a stub. To enable playback, install ffmpeg, PyNaCl and yt-dlp, then implement streaming using yt-dlp to get a direct stream url and pass it to discord.FFmpegPCMAudio.")

async def setup(bot):
    await bot.add_cog(MusicCog(bot))
