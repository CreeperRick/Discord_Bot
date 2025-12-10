# cogs/troll_enhanced.py
import discord
from discord.ext import commands, tasks
from discord import app_commands
import random
import asyncio

class TrollEnhanced(commands.Cog):
    """Harmless, rate-limited troll features. Admin-toggleable per guild."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _is_enabled(self, guild):
        from utils.db_async import DB
        return await DB.get_kv(guild.id, "troll_enabled", True)

    @commands.command(name="togglert")
    @commands.has_permissions(administrator=True)
    async def toggle_troll(self, ctx, enabled: bool):
        from utils.db_async import DB
        await DB.set_kv(ctx.guild.id, "troll_enabled", bool(enabled))
        await ctx.send(f"Troll features enabled={enabled}")

    @commands.command(name="ghostping")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def ghostping(self, ctx, member: discord.Member):
        """Mention a user then delete the mention quickly (one-off)."""
        if not await self._is_enabled(ctx.guild):
            return await ctx.send("Troll features disabled in this guild.")
        m = await ctx.send(f"{member.mention}")
        # Wait a short time and delete the ping message (safe ghost)
        await asyncio.sleep(1.2)
        try:
            await m.delete()
        except Exception:
            pass
        await ctx.send(f"👻 ghostping sent to {member.display_name} (one-time)", delete_after=6)

    @commands.command(name="faketype")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def faketype(self, ctx, *, text: str):
        """Fake typing animation then send text."""
        if not await self._is_enabled(ctx.guild):
            return await ctx.send("Troll features disabled in this guild.")
        async with ctx.typing():
            await asyncio.sleep(min(len(text) * 0.05, 5))
        await ctx.send(text)

    @commands.command(name="mock")
    async def mock(self, ctx, *, text: str):
        out = "".join(c.upper() if random.choice([True, False]) else c.lower() for c in text)
        await ctx.send(out)

    @commands.command(name="fakeerror")
    async def fakeerror(self, ctx, *, message="Unknown error"):
        emb = discord.Embed(title="Critical Error", description="An unrecoverable exception occurred.", color=discord.Color.dark_red())
        emb.add_field(name="Exception", value=message)
        emb.set_footer(text="Error code: 0xDEADBEEF (this is a prank)")
        await ctx.send(embed=emb)

    @commands.command(name="hackbar")
    async def hackbar(self, ctx, target: str = "target"):
        """Play a harmless 'hacking' progress bar animation (messages edited)."""
        msg = await ctx.send(f"Hacking `{target}`: [░░░░░░░░░░] 0%")
        steps = 10
        for i in range(1, steps + 1):
            await asyncio.sleep(0.6)
            pct = int(i / steps * 100)
            bar = "█" * i + "░" * (steps - i)
            await msg.edit(content=f"Hacking `{target}`: [{bar}] {pct}%")
        await msg.edit(content=f"Hacking complete. No data was harmed. ✅")

async def setup(bot):
    await bot.add_cog(TrollEnhanced(bot))
