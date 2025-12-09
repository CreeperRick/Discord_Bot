# utils/db.py
import json
from pathlib import Path
from typing import Any

DB_PATH = Path("data.json")

def _read_db() -> dict:
    if not DB_PATH.exists():
        return {}
    return json.loads(DB_PATH.read_text(encoding="utf-8"))

def _write_db(data: dict) -> None:
    DB_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def get(key: str, default=None):
    data = _read_db()
    return data.get(key, default)

def set(key: str, value: Any):
    data = _read_db()
    data[key] = value
    _write_db(data)

def delete(key: str):
    data = _read_db()
    if key in data:
        del data[key]
        _write_db(data)
