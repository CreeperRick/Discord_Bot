import asyncio
from quart import Quart, render_template, websocket, jsonify, request
import logging
from datetime import datetime
import json
from utils.database import Database
import aiofiles
import os

logger = logging.getLogger(__name__)

class WebDashboard:
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self.app = Quart(__name__)
        self.setup_routes()
        self.connected_clients = set()
        
    def setup_routes(self):
        # Main pages
        @self.app.route('/')
        async def index():
            return await render_template('index.html', 
                                       bot=self.bot,
                                       guilds=len(self.bot.guilds),
                                       uptime=datetime.now())
        
        @self.app.route('/dashboard')
        async def dashboard():
            stats = await self.db.get_bot_stats()
            return await render_template('dashboard.html',
                                       stats=stats,
                                       bot=self.bot)
        
        @self.app.route('/music')
        async def music_control():
            # Get music status from all guilds
            music_data = []
            for guild in self.bot.guilds:
                # Check if music cog is active in this guild
                music_cog = self.bot.get_cog('Music')
                if music_cog:
                    status = music_cog.get_guild_status(guild.id)
                    if status:
                        music_data.append(status)
            
            return await render_template('music.html',
                                       music_data=music_data,
                                       bot=self.bot)
        
        @self.app.route('/tickets')
        async def tickets():
            open_tickets = await self.db.get_open_tickets()
            return await render_template('tickets.html',
                                       tickets=open_tickets,
                                       bot=self.bot)
        
        @self.app.route('/moderation')
        async def moderation():
            logs = await self.db.get_moderation_logs(limit=100)
            return await render_template('moderation.html',
                                       logs=logs,
                                       bot=self.bot)
        
        @self.app.route('/settings')
        async def settings():
            bot_settings = await self.db.get_bot_settings()
            return await render_template('settings.html',
                                       settings=bot_settings,
                                       bot=self.bot)
        
        # API endpoints
        @self.app.route('/api/stats')
        async def api_stats():
            stats = {
                'guilds': len(self.bot.guilds),
                'users': sum(g.member_count for g in self.bot.guilds),
                'commands': len(self.bot.tree.get_commands()),
                'uptime': str(datetime.now()),
                'memory': '...',
                'cpu': '...'
            }
            return jsonify(stats)
        
        @self.app.route('/api/music/control', methods=['POST'])
        async def api_music_control():
            data = await request.get_json()
            action = data.get('action')
            guild_id = data.get('guild_id')
            
            # Control music playback
            music_cog = self.bot.get_cog('Music')
            if music_cog:
                success = await music_cog.web_control(guild_id, action, data)
                return jsonify({'success': success})
            
            return jsonify({'success': False, 'error': 'Music cog not loaded'})
        
        @self.app.route('/api/tickets/<action>', methods=['POST'])
        async def api_tickets_action(action):
            data = await request.get_json()
            ticket_id = data.get('ticket_id')
            
            tickets_cog = self.bot.get_cog('Tickets')
            if tickets_cog:
                result = await tickets_cog.web_action(action, ticket_id, data)
                return jsonify(result)
            
            return jsonify({'success': False})
        
        # WebSocket for real-time updates
        @self.app.websocket('/ws')
        async def ws():
            self.connected_clients.add(websocket._get_current_object())
            try:
                while True:
                    data = await websocket.receive()
                    # Handle incoming messages
                    if data:
                        await self.handle_websocket_message(data, websocket)
            finally:
                self.connected_clients.remove(websocket._get_current_object())
        
        # Static files
        @self.app.route('/static/<path:filename>')
        async def static_files(filename):
            return await self.app.send_static_file(filename)
    
    async def handle_websocket_message(self, data, ws):
        """Handle incoming WebSocket messages"""
        try:
            message = json.loads(data)
            msg_type = message.get('type')
            
            if msg_type == 'get_stats':
                stats = await self.db.get_bot_stats()
                await ws.send(json.dumps({
                    'type': 'stats_update',
                    'data': stats
                }))
                
        except json.JSONDecodeError:
            pass
    
    async def broadcast(self, data):
        """Broadcast data to all connected clients"""
        for client in self.connected_clients:
            try:
                await client.send(json.dumps(data))
            except:
                pass
    
    async def start(self, host='127.0.0.1', port=8080):
        """Start the web server"""
        logger.info(f'Starting web dashboard on http://{host}:{port}')
        await self.app.run_task(host=host, port=port, debug=False)

async def start_web_server(bot, db):
    """Start the web dashboard server"""
    dashboard = WebDashboard(bot, db)
    host = os.getenv('WEB_HOST', '127.0.0.1')
    port = int(os.getenv('WEB_PORT', 8080))
    
    # Start in background
    asyncio.create_task(dashboard.start(host, port))
    return dashboard
