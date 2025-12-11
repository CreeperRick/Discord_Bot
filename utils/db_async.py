import aiosqlite, asyncio, json, time
from pathlib import Path
DB_FILE = Path('botdata.sqlite3')

SCHEMA = [
'''CREATE TABLE IF NOT EXISTS kv (guild_id INTEGER, key TEXT, value TEXT, PRIMARY KEY (guild_id,key));''',
'''CREATE TABLE IF NOT EXISTS modlog (id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER, action TEXT, moderator_id INTEGER, target_id INTEGER, reason TEXT, timestamp INTEGER);''',
]

class DB:
    _conn = None
    _lock = asyncio.Lock()

    @classmethod
    async def conn(cls):
        async with cls._lock:
            if cls._conn is None:
                cls._conn = await aiosqlite.connect(str(DB_FILE))
                await cls._conn.execute('PRAGMA foreign_keys = ON;')
                for s in SCHEMA:
                    await cls._conn.execute(s)
                await cls._conn.commit()
            return cls._conn

    @classmethod
    async def get_kv(cls, guild_id:int, key:str, default=None):
        conn = await cls.conn()
        cur = await conn.execute('SELECT value FROM kv WHERE guild_id=? AND key=?', (guild_id, key))
        row = await cur.fetchone(); await cur.close()
        if not row: return default
        return json.loads(row[0])

    @classmethod
    async def set_kv(cls, guild_id:int, key:str, value):
        conn = await cls.conn()
        await conn.execute('INSERT OR REPLACE INTO kv (guild_id,key,value) VALUES (?,?,?)', (guild_id,key,json.dumps(value)))
        await conn.commit()

    @classmethod
    async def add_mod(cls, guild_id:int, action:str, moderator:int, target:int, reason:str):
        conn = await cls.conn()
        await conn.execute('INSERT INTO modlog (guild_id,action,moderator_id,target_id,reason,timestamp) VALUES (?,?,?,?,?,?)', (guild_id,action,moderator,target,reason,int(time.time())))
        await conn.commit()

    @classmethod
    async def get_mods(cls, guild_id:int, limit=50):
        conn = await cls.conn()
        cur = await conn.execute('SELECT id,action,moderator_id,target_id,reason,timestamp FROM modlog WHERE guild_id=? ORDER BY id DESC LIMIT ?', (guild_id,limit))
        rows = await cur.fetchall(); await cur.close(); return rows
