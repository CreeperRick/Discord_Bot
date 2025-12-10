# web_ui.py
import os
from aiohttp import web, ClientSession
import aiohttp_jinja2
import jinja2
from urllib.parse import urlencode
import secrets
import time
from utils.db_async import DB

DISCORD_API = "https://discord.com/api"

def create_web_app(bot, secret: str):
    app = web.Application()
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader("web_templates"))
    # secret for actions
    APP_SECRET = secret
    # oauth config from env
    CLIENT_ID = int(os.getenv("WEB_OAUTH_CLIENT_ID", "0"))
    CLIENT_SECRET = os.getenv("WEB_OAUTH_CLIENT_SECRET", "")
    REDIRECT = os.getenv("WEB_OAUTH_REDIRECT", "http://localhost:8080/oauth/callback")
    SESSIONS = {}  # in-memory session store: token -> {user,expires}

    def require_session(handler):
        async def wrapper(request):
            token = request.cookies.get("session_token")
            data = SESSIONS.get(token)
            if not data or data.get("expires",0) < time.time():
                # redirect to login
                raise web.HTTPFound(location="/login")
            request["user"] = data["user"]
            return await handler(request)
        return wrapper

    @aiohttp_jinja2.template("index.html")
    async def index(request):
        bot_user = None
        guilds = []
        if bot.is_ready():
            bot_user = {"name": str(bot.user), "id": bot.user.id}
            for g in bot.guilds:
                guilds.append({"id": g.id, "name": g.name, "member_count": g.member_count})
        return {"bot_user": bot_user, "guilds": guilds, "latency": round(bot.latency*1000) if bot.is_ready() else "N/A"}

    @aiohttp_jinja2.template("login.html")
    async def login(request):
        # show a login button linking to Discord OAuth2
        params = {
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT,
            "response_type": "code",
            "scope": "identify%20guilds",
            # consider adding "guilds.join" and other scopes for more features
        }
        url = f"https://discord.com/api/oauth2/authorize?{urlencode(params)}"
        return {"oauth_url": url}

    async def oauth_callback(request):
        code = request.query.get("code")
        if not code:
            return web.Response(text="No code provided")
        # exchange code for token
        async with ClientSession() as sess:
            data = {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT,
                "scope": "identify guilds",
            }
            headers = {"Content-Type":"application/x-www-form-urlencoded"}
            async with sess.post(DISCORD_API+"/oauth2/token", data=data, headers=headers) as resp:
                token_data = await resp.json()
            if "access_token" not in token_data:
                return web.Response(text=f"Token error: {token_data}")
            access_token = token_data["access_token"]
            # get user
            async with sess.get(DISCORD_API+"/users/@me", headers={"Authorization": f"Bearer {access_token}"}) as r:
                user = await r.json()
            # create session
            token = secrets.token_urlsafe(32)
            SESSIONS[token] = {"user": user, "expires": time.time() + 3600}
            res = web.HTTPFound(location="/")
            res.set_cookie("session_token", token, max_age=3600, httponly=True)
            return res

    @aiohttp_jinja2.template("settings.html")
    @require_session
    async def settings(request):
        # view guild-specific settings for guilds the user is in and bot is in
        user = request["user"]
        # get guilds from discord (sessions has guilds? we requested guilds scope - if not, ask API)
        # For simplicity: show guilds where bot is present
        user_guilds = []
        for g in request.app.get("bot").guilds:
            can_manage = True  # we can't verify the user's guild perms without further API calls; warn user
            troll_enabled = await DB.get_kv(g.id, "troll_enabled", True)
            modlog = await DB.get_kv(g.id, "modlog_channel", None)
            user_guilds.append({"id": g.id, "name": g.name, "troll_enabled": troll_enabled, "modlog": modlog})
        return {"user": user, "guilds": user_guilds}

    async def toggle_troll(request):
        # protected by secret + session
        data = await request.post()
        token = request.cookies.get("session_token")
        if not token or token not in SESSIONS:
            raise web.HTTPUnauthorized()
        # require secret in form
        if data.get("secret") != APP_SECRET:
            raise web.HTTPUnauthorized(text="Invalid secret")
        guild_id = int(data.get("guild_id"))
        enabled = data.get("enabled") == "true"
        await DB.set_kv(guild_id, "troll_enabled", enabled)
        raise web.HTTPFound(location="/settings")

    @aiohttp_jinja2.template("modlog.html")
    @require_session
    async def modlog_view(request):
        guild_id = int(request.match_info["guild_id"])
        logs = await DB.get_modlog(guild_id, limit=50)
        return {"logs": logs, "guild_id": guild_id}

    # register routes
    app.router.add_get("/", index)
    app.router.add_get("/login", login)
    app.router.add_get("/oauth/callback", oauth_callback)
    app.router.add_get("/settings", settings)
    app.router.add_post("/settings/toggle_troll", toggle_troll)
    app.router.add_get("/modlog/{guild_id:\d+}", modlog_view)

    # attach bot instance for settings()
    app["bot"] = bot

    return app
