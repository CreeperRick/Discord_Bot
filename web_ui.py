# web_ui.py
import os
from aiohttp import web
import aiohttp_jinja2
import jinja2
import json
import html

def create_web_app(bot, secret: str):
    """
    Create and return an aiohttp.web.Application that uses the provided `bot`.
    `secret` is a shared secret that must be provided when performing actions.
    """
    app = web.Application()
    # templates folder: ./web_templates
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader("web_templates"))

    # --- helper: require secret ---
    async def require_secret(request):
        # look for secret in either header 'X-SECRET' or form field 'secret'
        req_secret = request.headers.get("X-SECRET") or (await request.post()).get("secret", None)
        if req_secret != secret:
            raise web.HTTPUnauthorized(text="Invalid secret")
        return True

    # --- routes ---
    @aiohttp_jinja2.template("index.html")
    async def index(request):
        bot_user = None
        guilds = []
        if bot.is_ready():
            bot_user = {"name": str(bot.user), "id": bot.user.id}
            for g in bot.guilds:
                guilds.append({"id": g.id, "name": g.name, "member_count": g.member_count})
        return {
            "bot_user": bot_user,
            "guilds": guilds,
            "latency": round(bot.latency * 1000) if bot.is_ready() else "N/A"
        }

    @aiohttp_jinja2.template("guild.html")
    async def guild_view(request):
        guild_id = int(request.match_info["guild_id"])
        guild = bot.get_guild(guild_id)
        if guild is None:
            raise web.HTTPNotFound(text="Guild not found or bot not in guild")
        channels = []
        for ch in guild.text_channels:
            channels.append({"id": ch.id, "name": ch.name})
        return {"guild": {"id": guild.id, "name": guild.name}, "channels": channels, "secret": secret}

    async def send_message(request):
        # POST only
        await require_secret(request)
        data = await request.post()
        guild_id = int(data.get("guild_id"))
        channel_id = int(data.get("channel_id"))
        content = data.get("content", "").strip()
        if not content:
            raise web.HTTPBadRequest(text="No content")
        guild = bot.get_guild(guild_id)
        if not guild:
            raise web.HTTPNotFound(text="Guild not found")
        channel = guild.get_channel(channel_id)
        if not channel:
            raise web.HTTPNotFound(text="Channel not found")
        # ensure it's a text channel and bot can send
        try:
            await channel.send(content)
        except Exception as e:
            raise web.HTTPInternalServerError(text=f"Failed to send message: {e}")
        # redirect back to guild view
        raise web.HTTPFound(location=f"/guilds/{guild_id}")

    # basic JSON API endpoints (protected)
    async def api_status(request):
        if not bot.is_ready():
            return web.json_response({"ready": False})
        return web.json_response({
            "ready": True,
            "user": {"id": bot.user.id, "name": str(bot.user)},
            "guild_count": len(bot.guilds),
            "latency_ms": round(bot.latency * 1000)
        })

    async def api_guilds(request):
        await require_secret(request)
        return web.json_response([{"id": g.id, "name": g.name, "member_count": g.member_count} for g in bot.guilds])

    # register routes
    app.router.add_get("/", index)
    app.router.add_get("/guilds/{guild_id:\d+}", guild_view)
    app.router.add_post("/send_message", send_message)
    app.router.add_get("/api/status", api_status)
    app.router.add_get("/api/guilds", api_guilds)

    # static for minimal CSS (if needed)
    app.router.add_static("/static", os.path.join(os.path.dirname(__file__), "web_static"), show_index=True)

    return app
