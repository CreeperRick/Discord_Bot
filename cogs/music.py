import discord
from discord.ext import commands
from typing import Dict, List

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues: Dict[int, List[dict]] = {}

    @commands.command(name="join")
    async def join(self, ctx):
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send("You must be in a voice channel.")
        channel = ctx.author.voice.channel
        vc = ctx.voice_client
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

    @commands.command(name="add")
    async def add(self, ctx, *, query: str):
        self.queues.setdefault(ctx.guild.id, []).append({"title": query, "requester": ctx.author.id})
        await ctx.send(f"Added to queue: {query}")

    @commands.command(name="queue")
    async def queue_cmd(self, ctx):
        q = self.queues.get(ctx.guild.id, [])
        if not q:
            return await ctx.send("Queue empty.")
        await ctx.send("\n".join(f"{i+1}. {t['title']}" for i,t in enumerate(q[:10])))

    @commands.command(name="play")
    async def play(self, ctx):
        await ctx.send("Playback disabled by default. Install ffmpeg, PyNaCl and yt-dlp then enable streaming implementation.")

async def setup(bot):
    await bot.add_cog(Music(bot))
