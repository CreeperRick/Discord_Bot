import os, secrets, time, json
from aiohttp import web, ClientSession
import aiohttp_jinja2, jinja2
from urllib.parse import urlencode
from utils.db_async import DB

DISCORD_API = 'https://discord.com/api'
REDIS_URL = os.getenv('REDIS_URL', None)

async def get_redis():
    if not REDIS_URL:
        return None
    import aioredis
    return aioredis.from_url(REDIS_URL, encoding='utf-8', decode_responses=True)

def create_app(bot, secret):
    app = web.Application()
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('web_templates'))
    CLIENT_ID = os.getenv('WEB_OAUTH_CLIENT_ID','')
    CLIENT_SECRET = os.getenv('WEB_OAUTH_CLIENT_SECRET','')
    REDIRECT = os.getenv('WEB_OAUTH_REDIRECT','http://localhost:5000/oauth/callback')

    SESSIONS = {}

    async def session_get(token):
        r = await get_redis()
        if r:
            data = await r.get(f'session:{token}')
            if data:
                return json.loads(data)
            return None
        return SESSIONS.get(token)

    async def session_set(token, data, ttl=3600):
        r = await get_redis()
        if r:
            await r.set(f'session:{token}', json.dumps(data), ex=ttl)
        else:
            SESSIONS[token] = data

    def require_session(handler):
        async def wrapper(request):
            token = request.cookies.get('session_token')
            if not token:
                raise web.HTTPFound('/login')
            data = await session_get(token)
            if not data or data.get('expires',0) < time.time():
                raise web.HTTPFound('/login')
            request['user'] = data['user']
            return await handler(request)
        return wrapper

    @aiohttp_jinja2.template('index.html')
    async def index(request):
        bot_user = None; guilds = []
        if bot.is_ready():
            bot_user = {'name':str(bot.user),'id':bot.user.id}
            for g in bot.guilds:
                guilds.append({'id':g.id,'name':g.name,'members':g.member_count})
        return {'bot_user':bot_user,'guilds':guilds,'latency':round(bot.latency*1000) if bot.is_ready() else 'N/A'}

    @aiohttp_jinja2.template('login.html')
    async def login(request):
        params = {'client_id':CLIENT_ID,'redirect_uri':REDIRECT,'response_type':'code','scope':'identify guilds'}
        url = f"{DISCORD_API}/oauth2/authorize?{urlencode(params)}"
        return {'oauth_url':url}

    async def oauth_callback(request):
        code = request.query.get('code')
        if not code: return web.Response(text='Missing code')
        async with ClientSession() as sess:
            data = {'client_id':CLIENT_ID,'client_secret':CLIENT_SECRET,'grant_type':'authorization_code','code':code,'redirect_uri':REDIRECT}
            headers = {'Content-Type':'application/x-www-form-urlencoded'}
            async with sess.post(f'{DISCORD_API}/oauth2/token', data=data, headers=headers) as r:
                token = await r.json()
            if 'access_token' not in token: return web.Response(text=f'OAuth error: {token}')
            async with sess.get(f'{DISCORD_API}/users/@me', headers={'Authorization':f"Bearer {token['access_token']}"}) as r:
                user = await r.json()
            tok = secrets.token_urlsafe(24)
            await session_set(tok, {'user':user, 'expires': time.time()+3600}, ttl=3600)
            res = web.HTTPFound('/settings'); res.set_cookie('session_token', tok, max_age=3600, httponly=True)
            return res

    @aiohttp_jinja2.template('settings.html')
    @require_session
    async def settings(request):
        user = request['user']; guilds = []
        for g in bot.guilds:
            troll = await DB.get_kv(g.id, 'troll_enabled', True)
            guilds.append({'id':g.id,'name':g.name,'troll':troll})
        return {'user':user,'guilds':guilds,'secret':secret}

    async def toggle_troll(request):
        data = await request.post(); token = request.cookies.get('session_token')
        if not token: raise web.HTTPUnauthorized()
        d = await session_get(token)
        if not d: raise web.HTTPUnauthorized()
        if data.get('secret') != secret: raise web.HTTPUnauthorized()
        gid = int(data.get('guild_id')); enabled = data.get('enabled') == 'true'
        await DB.set_kv(gid, 'troll_enabled', enabled)
        raise web.HTTPFound('/settings')

    @aiohttp_jinja2.template('modlog.html')
    @require_session
    async def modlog(request):
        gid = int(request.match_info['guild_id'])
        logs = await DB.get_mods(gid, limit=100)
        return {'logs':logs}

    app.router.add_get('/', index)
    app.router.add_get('/login', login)
    app.router.add_get('/oauth/callback', oauth_callback)
    app.router.add_get('/settings', settings)
    app.router.add_post('/settings/toggle_troll', toggle_troll)
    app.router.add_get('/modlog/{guild_id:\d+}', modlog)
    return app
