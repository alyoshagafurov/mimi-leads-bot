"""Async SQLite storage for leads (self-contained, via aiosqlite)."""
from datetime import datetime, timezone

import aiosqlite

from .config import get_settings

settings = get_settings()

VALID_STATUSES = ("new", "in_progress", "done")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    contact    TEXT NOT NULL,
    message    TEXT NOT NULL,
    source     TEXT NOT NULL DEFAULT 'telegram-bot',
    status     TEXT NOT NULL DEFAULT 'new',
    created_at TEXT NOT NULL
);
"""


async def init_db() -> None:
    async with aiosqlite.connect(settings.database_path) as db:
        await db.execute(_SCHEMA)
        await db.commit()


async def add_lead(name: str, contact: str, message: str, source: str = "telegram-bot") -> int:
    created_at = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(settings.database_path) as db:
        cursor = await db.execute(
            "INSERT INTO leads (name, contact, message, source, status, created_at) "
            "VALUES (?, ?, ?, ?, 'new', ?)",
            (name, contact, message, source, created_at),
        )
        await db.commit()
        return cursor.lastrowid


async def list_leads(limit: int = 10) -> list[dict]:
    async with aiosqlite.connect(settings.database_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM leads ORDER BY id DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_lead(lead_id: int) -> dict | None:
    async with aiosqlite.connect(settings.database_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def update_status(lead_id: int, status: str) -> None:
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {status}")
    async with aiosqlite.connect(settings.database_path) as db:
        await db.execute(
            "UPDATE leads SET status = ? WHERE id = ?", (status, lead_id)
        )
        await db.commit()


async def stats() -> dict[str, int]:
    result = {status: 0 for status in VALID_STATUSES}
    async with aiosqlite.connect(settings.database_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT status, COUNT(*) AS cnt FROM leads GROUP BY status"
        )
        for row in await cursor.fetchall():
            if row["status"] in result:
                result[row["status"]] = row["cnt"]
    return result
