# utils/db_async.py
import aiosqlite
import asyncio
import json
from pathlib import Path
from typing import Any, Optional, List, Dict

DB_FILE = Path("botdata.sqlite3")

CREATE_TABLES_SQL = [
    """
    CREATE TABLE IF NOT EXISTS kv_store (
      guild_id INTEGER,
      key TEXT,
      value TEXT,
      PRIMARY KEY (guild_id, key)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS modlog (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      guild_id INTEGER,
      action TEXT,
      moderator_id INTEGER,
      target_id INTEGER,
      reason TEXT,
      timestamp INTEGER
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS afk (
      guild_id INTEGER,
      user_id INTEGER,
      note TEXT,
      since INTEGER,
      PRIMARY KEY (guild_id, user_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS economy (
      guild_id INTEGER,
      user_id INTEGER,
      balance INTEGER DEFAULT 0,
      PRIMARY KEY (guild_id, user_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS starboard (
      guild_id INTEGER,
      message_id INTEGER,
      channel_id INTEGER,
      star_count INTEGER,
      PRIMARY KEY (guild_id, message_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS reminders (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      guild_id INTEGER,
      user_id INTEGER,
      content TEXT,
      remind_at INTEGER
    );
    """
]

class DB:
    _conn: Optional[aiosqlite.Connection] = None
    _lock = asyncio.Lock()

    @classmethod
    async def get_conn(cls):
        async with cls._lock:
            if cls._conn is None:
                cls._conn = await aiosqlite.connect(str(DB_FILE))
                await cls._conn.execute("PRAGMA foreign_keys = ON;")
                # apply migrations / create tables
                for sql in CREATE_TABLES_SQL:
                    await cls._conn.execute(sql)
                await cls._conn.commit()
            return cls._conn

    @classmethod
    async def get_kv(cls, guild_id: int, key: str, default=None):
        conn = await cls.get_conn()
        cur = await conn.execute("SELECT value FROM kv_store WHERE guild_id = ? AND key = ?", (guild_id, key))
        row = await cur.fetchone()
        await cur.close()
        if not row:
            return default
        return json.loads(row[0])

    @classmethod
    async def set_kv(cls, guild_id: int, key: str, value: Any):
        conn = await cls.get_conn()
        v = json.dumps(value)
        await conn.execute(
            "INSERT OR REPLACE INTO kv_store (guild_id, key, value) VALUES (?, ?, ?)",
            (guild_id, key, v)
        )
        await conn.commit()

    @classmethod
    async def add_modlog(cls, guild_id:int, action:str, moderator_id:int, target_id:int, reason:str, ts:int):
        conn = await cls.get_conn()
        await conn.execute(
            "INSERT INTO modlog (guild_id, action, moderator_id, target_id, reason, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
            (guild_id, action, moderator_id, target_id, reason, ts)
        )
        await conn.commit()

    @classmethod
    async def get_modlog(cls, guild_id:int, limit:int=50) -> List[Dict]:
        conn = await cls.get_conn()
        cur = await conn.execute("SELECT id, action, moderator_id, target_id, reason, timestamp FROM modlog WHERE guild_id = ? ORDER BY id DESC LIMIT ?", (guild_id, limit))
        rows = await cur.fetchall()
        await cur.close()
        return [
            {"id": r[0], "action": r[1], "moderator_id": r[2], "target_id": r[3], "reason": r[4], "timestamp": r[5]}
            for r in rows
        ]

    @classmethod
    async def set_afk(cls, guild_id:int, user_id:int, note:str, since:int):
        conn = await cls.get_conn()
        await conn.execute("INSERT OR REPLACE INTO afk (guild_id, user_id, note, since) VALUES (?, ?, ?, ?)", (guild_id, user_id, note, since))
        await conn.commit()

    @classmethod
    async def get_afk(cls, guild_id:int, user_id:int):
        conn = await cls.get_conn()
        cur = await conn.execute("SELECT note, since FROM afk WHERE guild_id=? AND user_id=?", (guild_id, user_id))
        row = await cur.fetchone()
        await cur.close()
        if not row:
            return None
        return {"note": row[0], "since": row[1]}

    @classmethod
    async def remove_afk(cls, guild_id:int, user_id:int):
        conn = await cls.get_conn()
        await conn.execute("DELETE FROM afk WHERE guild_id=? AND user_id=?", (guild_id, user_id))
        await conn.commit()

    # economy helpers
    @classmethod
    async def get_balance(cls, guild_id:int, user_id:int):
        conn = await cls.get_conn()
        cur = await conn.execute("SELECT balance FROM economy WHERE guild_id=? AND user_id=?", (guild_id, user_id))
        row = await cur.fetchone()
        await cur.close()
        if row:
            return row[0]
        # initialize
        await conn.execute("INSERT OR REPLACE INTO economy (guild_id, user_id, balance) VALUES (?, ?, ?)", (guild_id, user_id, 0))
        await conn.commit()
        return 0

    @classmethod
    async def add_balance(cls, guild_id:int, user_id:int, amount:int):
        conn = await cls.get_conn()
        bal = await cls.get_balance(guild_id, user_id)
        new = bal + amount
        await conn.execute("INSERT OR REPLACE INTO economy (guild_id, user_id, balance) VALUES (?, ?, ?)", (guild_id, user_id, new))
        await conn.commit()
        return new

    # reminders
    @classmethod
    async def add_reminder(cls, guild_id:int, user_id:int, content:str, remind_at:int):
        conn = await cls.get_conn()
        cur = await conn.execute("INSERT INTO reminders (guild_id, user_id, content, remind_at) VALUES (?, ?, ?, ?)", (guild_id, user_id, content, remind_at))
        await conn.commit()
        return cur.lastrowid

    @classmethod
    async def get_due_reminders(cls, now_ts:int):
        conn = await cls.get_conn()
        cur = await conn.execute("SELECT id, guild_id, user_id, content FROM reminders WHERE remind_at <= ?", (now_ts,))
        rows = await cur.fetchall()
        await cur.close()
        return rows

    @classmethod
    async def delete_reminder(cls, id:int):
        conn = await cls.get_conn()
        await conn.execute("DELETE FROM reminders WHERE id = ?", (id,))
        await conn.commit()
