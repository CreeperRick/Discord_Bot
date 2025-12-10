import os, secrets, time
from aiohttp import web, ClientSession
import aiohttp_jinja2, jinja2
from urllib.parse import urlencode
from utils.db_async import DB

DISCORD_API = "https://discord.com/api"

def create_web_app(bot, secret: str):
    app = web.Application()
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader("web_templates"))
    CLIENT_ID = os.getenv("WEB_OAUTH_CLIENT_ID", "")
    CLIENT_SECRET = os.getenv("WEB_OAUTH_CLIENT_SECRET", "")
    REDIRECT = os.getenv("WEB_OAUTH_REDIRECT", "http://localhost:5000/oauth/callback")
    SESSIONS = {}

    def require_session(handler):
        async def wrapper(request):
            token = request.cookies.get("session_token")
            session = SESSIONS.get(token)
            if not session or session.get("expires",0) < time.time():
                raise web.HTTPFound(location="/login")
            request["user"] = session["user"]
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
        params = {
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT,
            "response_type": "code",
            "scope": "identify guilds"
        }
        url = f"{DISCORD_API}/oauth2/authorize?{urlencode(params)}"
        return {"oauth_url": url}

    async def oauth_callback(request):
        code = request.query.get("code")
        if not code:
            return web.Response(text="Missing code.")
        async with ClientSession() as sess:
            data = {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT,
            }
            headers = {"Content-Type":"application/x-www-form-urlencoded"}
            async with sess.post(DISCORD_API + "/oauth2/token", data=data, headers=headers) as r:
                token_data = await r.json()
            if "access_token" not in token_data:
                return web.Response(text=f"OAuth error: {token_data}")
            access_token = token_data["access_token"]
            async with sess.get(DISCORD_API + "/users/@me", headers={"Authorization": f"Bearer {access_token}"}) as r:
                user = await r.json()
            tok = secrets.token_urlsafe(24)
            SESSIONS[tok] = {"user": user, "expires": time.time() + 3600}
            res = web.HTTPFound(location="/settings")
            res.set_cookie("session_token", tok, max_age=3600, httponly=True)
            return res

    @aiohttp_jinja2.template("settings.html")
    @require_session
    async def settings(request):
        user = request["user"]
        user_guilds = []
        for g in bot.guilds:
            troll_enabled = await DB.get_kv(g.id, "troll_enabled", True)
            modlog = await DB.get_kv(g.id, "modlog_channel", None)
            user_guilds.append({"id": g.id, "name": g.name, "troll_enabled": troll_enabled, "modlog": modlog})
        return {"user": user, "guilds": user_guilds, "secret": secret}

    async def toggle_troll(request):
        data = await request.post()
        token = request.cookies.get("session_token")
        if token is None:
            raise web.HTTPUnauthorized()
        if data.get("secret") != secret:
            raise web.HTTPUnauthorized()
        gid = int(data.get("guild_id"))
        enabled = data.get("enabled") == "true"
        await DB.set_kv(gid, "troll_enabled", enabled)
        raise web.HTTPFound(location="/settings")

    @aiohttp_jinja2.template("modlog.html")
    @require_session
    async def modlog_view(request):
        gid = int(request.match_info["guild_id"])
        logs = await DB.get_modlog(gid, limit=100)
        return {"logs": logs}

    async def api_status(request):
        return web.json_response({
            "ready": bot.is_ready(),
            "user": str(bot.user) if bot.is_ready() else None,
            "guild_count": len(bot.guilds)
        })

    app.router.add_get("/", index)
    app.router.add_get("/login", login)
    app.router.add_get("/oauth/callback", oauth_callback)
    app.router.add_get("/settings", settings)
    app.router.add_post("/settings/toggle_troll", toggle_troll)
    app.router.add_get("/modlog/{guild_id:\d+}", modlog_view)
    app.router.add_get("/api/status", api_status)

    app["bot"] = bot
    return app
