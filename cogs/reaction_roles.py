import discord
from discord.ext import commands
from utils.db_async import DB

class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="reactadd")
    @commands.has_permissions(manage_roles=True)
    async def reactadd(self, ctx: commands.Context, message_id:int, emoji: str, role: discord.Role):
        conn = await DB.get_conn()
        await conn.execute("INSERT OR REPLACE INTO reaction_roles (guild_id, message_id, emoji, role_id) VALUES (?, ?, ?, ?)", (ctx.guild.id, message_id, emoji, role.id))
        await conn.commit()
        await ctx.send("Reaction role added.")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.member and payload.member.bot:
            return
        conn = await DB.get_conn()
        cur = await conn.execute("SELECT role_id FROM reaction_roles WHERE guild_id=? AND message_id=? AND emoji=?", (payload.guild_id, payload.message_id, str(payload.emoji)))
        row = await cur.fetchone()
        await cur.close()
        if row:
            guild = self.bot.get_guild(payload.guild_id)
            role = guild.get_role(row[0])
            member = guild.get_member(payload.user_id)
            if role and member:
                try:
                    await member.add_roles(role, reason="Reaction role")
                except:
                    pass

async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))
