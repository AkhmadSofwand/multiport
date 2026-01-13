from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional

import aiosqlite


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def dt_to_str(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


class AgentDB:
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)

    async def connect(self) -> aiosqlite.Connection:
        db = await aiosqlite.connect(self.path)
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA journal_mode=WAL;")
        return db

    async def init(self) -> None:
        db = await self.connect()
        try:
            await db.executescript(
                """
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    protocol TEXT NOT NULL,
                    username TEXT NOT NULL,
                    secret TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                );
                """
            )
            await db.commit()
        finally:
            await db.close()

    async def add_account(self, protocol: str, username: str, secret: str, created_at: str, expires_at: str) -> None:
        db = await self.connect()
        try:
            await db.execute(
                "INSERT INTO accounts (protocol, username, secret, created_at, expires_at) VALUES (?, ?, ?, ?, ?)",
                (protocol, username, secret, created_at, expires_at),
            )
            await db.commit()
        finally:
            await db.close()

    async def count_active(self) -> int:
        db = await self.connect()
        try:
            now = dt_to_str(utcnow())
            cur = await db.execute("SELECT COUNT(*) AS c FROM accounts WHERE expires_at > ?", (now,))
            row = await cur.fetchone()
            return int(row["c"]) if row else 0
        finally:
            await db.close()

    async def list_expired(self) -> list[dict]:
        db = await self.connect()
        try:
            now = dt_to_str(utcnow())
            cur = await db.execute("SELECT * FROM accounts WHERE expires_at <= ?", (now,))
            rows = await cur.fetchall()
            return [dict(r) for r in rows]
        finally:
            await db.close()

    async def delete_account(self, account_id: int) -> None:
        db = await self.connect()
        try:
            await db.execute("DELETE FROM accounts WHERE id=?", (account_id,))
            await db.commit()
        finally:
            await db.close()
