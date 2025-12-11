import os, secrets, time, json
from aiohttp import web, ClientSession
import aiohttp_jinja2, jinja2
from urllib.parse import urlencode
from utils.db_async import DB

DISCORD_API = 'https://discord.com/api'

async def create_app(bot, secret):
    app = web.Application()
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('web_templates'))

    @aiohttp_jinja2.template('index.html')
    async def index(request):
        return {'ready': bot.is_ready(), 'guilds': [{'id':g.id,'name':g.name} for g in bot.guilds]}

    app.router.add_get('/', index)
    app['bot'] = bot
    return app
