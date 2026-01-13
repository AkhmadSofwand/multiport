\
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

import aiosqlite


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def dt_to_str(dt: datetime | None) -> str | None:
    return dt.astimezone(timezone.utc).isoformat() if dt else None


def str_to_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


@dataclass
class User:
    user_id: int
    first_name: str | None
    username: str | None
    language: str
    joined_at: str
    is_blocked: int
    is_subscribed: int
    subscribed_at: str | None
    agreement_accepted: int
    agreement_accepted_at: str | None
    credits: int
    vip_coins: int
    points: int
    last_checkin_date: str | None
    referrals_count: int
    referred_by: int | None
    total_spent: float
    star_active_until: str | None
    unpaid_invoices: int


class Database:
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)

    async def connect(self) -> aiosqlite.Connection:
        db = await aiosqlite.connect(self.path)
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA journal_mode=WAL;")
        await db.execute("PRAGMA foreign_keys=ON;")
        return db

    async def init(self) -> None:
        db = await self.connect()
        try:
            await db.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    first_name TEXT,
                    username TEXT,
                    language TEXT NOT NULL DEFAULT 'ms',
                    joined_at TEXT NOT NULL,
                    is_blocked INTEGER NOT NULL DEFAULT 0,
                    is_subscribed INTEGER NOT NULL DEFAULT 0,
                    subscribed_at TEXT,
                    agreement_accepted INTEGER NOT NULL DEFAULT 0,
                    agreement_accepted_at TEXT,
                    credits INTEGER NOT NULL DEFAULT 0,
                    vip_coins INTEGER NOT NULL DEFAULT 0,
                    points INTEGER NOT NULL DEFAULT 0,
                    last_checkin_date TEXT,
                    referrals_count INTEGER NOT NULL DEFAULT 0,
                    referred_by INTEGER,
                    total_spent REAL NOT NULL DEFAULT 0,
                    star_active_until TEXT,
                    unpaid_invoices INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS referrals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referrer_id INTEGER NOT NULL,
                    referred_id INTEGER NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    qualified INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS servers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pool TEXT NOT NULL, -- FREE | STAR
                    name TEXT NOT NULL,
                    base_url TEXT NOT NULL,
                    api_key TEXT NOT NULL,
                    max_users INTEGER NOT NULL DEFAULT 100,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    last_notified_full INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    type TEXT NOT NULL, -- vip_coin | star
                    amount_myr REAL NOT NULL,
                    qty INTEGER NOT NULL,
                    bill_code TEXT NOT NULL,
                    bill_url TEXT NOT NULL,
                    status TEXT NOT NULL, -- pending | paid | expired
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    paid_at TEXT,
                    meta_json TEXT
                );

                CREATE TABLE IF NOT EXISTS claims (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    protocol TEXT NOT NULL, -- ssh|vless|trojan
                    days INTEGER NOT NULL,
                    channel TEXT NOT NULL, -- free|vip|star|convert
                    server_id INTEGER,
                    created_at TEXT NOT NULL,
                    cost_credits INTEGER NOT NULL DEFAULT 0,
                    cost_vip_coins INTEGER NOT NULL DEFAULT 0,
                    result_json TEXT
                );

                CREATE TABLE IF NOT EXISTS support_map (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_message_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            await db.commit()
        finally:
            await db.close()

    async def get_user(self, user_id: int) -> User | None:
        db = await self.connect()
        try:
            cur = await db.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
            row = await cur.fetchone()
            if not row:
                return None
            return User(**dict(row))
        finally:
            await db.close()

    async def upsert_user(self, user_id: int, first_name: str | None, username: str | None, referred_by: int | None = None) -> User:
        now = dt_to_str(utcnow())
        db = await self.connect()
        try:
            cur = await db.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
            row = await cur.fetchone()
            if row:
                await db.execute(
                    "UPDATE users SET first_name=?, username=? WHERE user_id=?",
                    (first_name, username, user_id),
                )
                await db.commit()
                return User(**dict(row))
            await db.execute(
                """
                INSERT INTO users (user_id, first_name, username, joined_at, referred_by)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, first_name, username, now, referred_by),
            )
            await db.commit()
            return (await self.get_user(user_id))  # type: ignore
        finally:
            await db.close()

    async def set_language(self, user_id: int, lang: str) -> None:
        db = await self.connect()
        try:
            await db.execute("UPDATE users SET language=? WHERE user_id=?", (lang, user_id))
            await db.commit()
        finally:
            await db.close()

    async def mark_subscribed(self, user_id: int, give_credit_if_first: bool = True) -> Tuple[bool, bool]:
        """
        Returns (is_first_time_subscribe, gave_credit)
        """
        db = await self.connect()
        try:
            cur = await db.execute("SELECT is_subscribed, credits FROM users WHERE user_id=?", (user_id,))
            row = await cur.fetchone()
            if not row:
                return (False, False)
            is_subscribed = int(row["is_subscribed"]) == 1
            if is_subscribed:
                return (False, False)
            # first time
            gave_credit = False
            if give_credit_if_first:
                await db.execute(
                    "UPDATE users SET is_subscribed=1, subscribed_at=?, credits=credits+1 WHERE user_id=?",
                    (dt_to_str(utcnow()), user_id),
                )
                gave_credit = True
            else:
                await db.execute(
                    "UPDATE users SET is_subscribed=1, subscribed_at=? WHERE user_id=?",
                    (dt_to_str(utcnow()), user_id),
                )
            await db.commit()
            return (True, gave_credit)
        finally:
            await db.close()

    async def accept_agreement(self, user_id: int) -> None:
        db = await self.connect()
        try:
            await db.execute(
                "UPDATE users SET agreement_accepted=1, agreement_accepted_at=? WHERE user_id=?",
                (dt_to_str(utcnow()), user_id),
            )
            await db.commit()
        finally:
            await db.close()

    async def add_credits(self, user_id: int, delta: int) -> None:
        db = await self.connect()
        try:
            await db.execute("UPDATE users SET credits=credits+? WHERE user_id=?", (delta, user_id))
            await db.commit()
        finally:
            await db.close()

    async def add_vip_coins(self, user_id: int, delta: int) -> None:
        db = await self.connect()
        try:
            await db.execute("UPDATE users SET vip_coins=vip_coins+? WHERE user_id=?", (delta, user_id))
            await db.commit()
        finally:
            await db.close()

    async def set_star_until(self, user_id: int, until_dt: datetime) -> None:
        db = await self.connect()
        try:
            await db.execute("UPDATE users SET star_active_until=? WHERE user_id=?", (dt_to_str(until_dt), user_id))
            await db.commit()
        finally:
            await db.close()

    async def increment_total_spent(self, user_id: int, amount_myr: float) -> None:
        db = await self.connect()
        try:
            await db.execute("UPDATE users SET total_spent=total_spent+? WHERE user_id=?", (amount_myr, user_id))
            await db.commit()
        finally:
            await db.close()

    async def set_blocked(self, user_id: int, blocked: bool) -> None:
        db = await self.connect()
        try:
            await db.execute("UPDATE users SET is_blocked=? WHERE user_id=?", (1 if blocked else 0, user_id))
            await db.commit()
        finally:
            await db.close()

    async def add_unpaid_strike(self, user_id: int) -> int:
        db = await self.connect()
        try:
            await db.execute("UPDATE users SET unpaid_invoices=unpaid_invoices+1 WHERE user_id=?", (user_id,))
            await db.commit()
            cur = await db.execute("SELECT unpaid_invoices FROM users WHERE user_id=?", (user_id,))
            row = await cur.fetchone()
            return int(row["unpaid_invoices"]) if row else 0
        finally:
            await db.close()

    async def reset_unpaid_strikes(self, user_id: int) -> None:
        db = await self.connect()
        try:
            await db.execute("UPDATE users SET unpaid_invoices=0 WHERE user_id=?", (user_id,))
            await db.commit()
        finally:
            await db.close()

    async def record_referral(self, referrer_id: int, referred_id: int) -> None:
        db = await self.connect()
        try:
            # prevent self-ref
            if referrer_id == referred_id:
                return
            # only insert if not exists
            cur = await db.execute("SELECT 1 FROM referrals WHERE referred_id=?", (referred_id,))
            if await cur.fetchone():
                return
            await db.execute(
                "INSERT INTO referrals (referrer_id, referred_id, created_at, qualified) VALUES (?, ?, ?, 0)",
                (referrer_id, referred_id, dt_to_str(utcnow())),
            )
            await db.commit()
        finally:
            await db.close()

    async def qualify_referral_if_needed(self, referred_id: int) -> Optional[int]:
        """
        Called when referred user becomes subscribed.
        Returns referrer_id if newly qualified, else None.
        """
        db = await self.connect()
        try:
            cur = await db.execute(
                "SELECT referrer_id, qualified FROM referrals WHERE referred_id=?",
                (referred_id,),
            )
            row = await cur.fetchone()
            if not row:
                return None
            if int(row["qualified"]) == 1:
                return None
            referrer_id = int(row["referrer_id"])
            await db.execute("UPDATE referrals SET qualified=1 WHERE referred_id=?", (referred_id,))
            # increase referrer count
            await db.execute("UPDATE users SET referrals_count=referrals_count+1 WHERE user_id=?", (referrer_id,))
            await db.commit()
            return referrer_id
        finally:
            await db.close()

    async def get_referrals_count(self, user_id: int) -> int:
        db = await self.connect()
        try:
            cur = await db.execute("SELECT referrals_count FROM users WHERE user_id=?", (user_id,))
            row = await cur.fetchone()
            return int(row["referrals_count"]) if row else 0
        finally:
            await db.close()

    async def maybe_award_referral_credit(self, referrer_id: int, max_refs: int = 90) -> Optional[int]:
        """
        Every 3 qualified referrals -> +1 credit (up to 90 referrals).
        Returns credits_awarded (0/1) or None if not eligible.
        """
        db = await self.connect()
        try:
            cur = await db.execute("SELECT referrals_count FROM users WHERE user_id=?", (referrer_id,))
            row = await cur.fetchone()
            if not row:
                return None
            refs = int(row["referrals_count"])
            if refs > max_refs:
                refs = max_refs
            # compute how many credits should be earned
            should_have = refs // 3
            # track already awarded via (credits earned from referrals) is not stored separately; we derive from claims?
            # To keep it simple, store awarded credits in meta field? We'll store in users.points? no.
            # We'll add a hidden column via user table? Not available. We'll store in referrals table maybe? Not.
            # Quick solution: store in users.total_spent negative? No.
            # We'll approximate by storing awarded credits as (refs_awarded_credits) in points? hmm.
            # We'll add a new table for settings? Instead, we can store it in users.unpaid_invoices?? no.
            # For now, we will store awarded credits count in users.points if >0? not.
            # We'll add a new column safely by ALTER TABLE at init? Not.
            #
            # We'll store awarded credits in a separate table key-value.
            await db.execute(
                "CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT NOT NULL)"
            )
            key = f"ref_awarded:{referrer_id}"
            cur2 = await db.execute("SELECT v FROM kv WHERE k=?", (key,))
            r2 = await cur2.fetchone()
            awarded = int(r2["v"]) if r2 else 0
            if should_have <= awarded:
                return 0
            delta = should_have - awarded
            # award delta credits, but to avoid huge batch, cap to 1 at a time
            if delta > 0:
                await db.execute("UPDATE users SET credits=credits+1 WHERE user_id=?", (referrer_id,))
                await db.execute("INSERT OR REPLACE INTO kv (k, v) VALUES (?, ?)", (key, str(awarded + 1)))
                await db.commit()
                return 1
            return 0
        finally:
            await db.close()

    async def can_checkin_today(self, user_id: int) -> bool:
        db = await self.connect()
        try:
            cur = await db.execute("SELECT last_checkin_date FROM users WHERE user_id=?", (user_id,))
            row = await cur.fetchone()
            if not row:
                return False
            last = row["last_checkin_date"]
            today = utcnow().date().isoformat()
            return (last != today)
        finally:
            await db.close()

    async def do_checkin(self, user_id: int) -> int:
        """
        +1 point. Every 30 points => +1 credit (auto convert).
        Returns current points.
        """
        db = await self.connect()
        try:
            today = utcnow().date().isoformat()
            # set last_checkin_date and increment points
            await db.execute("UPDATE users SET points=points+1, last_checkin_date=? WHERE user_id=?", (today, user_id))
            # auto convert to credits
            cur = await db.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
            row = await cur.fetchone()
            points = int(row["points"]) if row else 0
            if points >= 30:
                credits_add = points // 30
                points_rem = points % 30
                await db.execute("UPDATE users SET credits=credits+?, points=? WHERE user_id=?", (credits_add, points_rem, user_id))
                points = points_rem
            await db.commit()
            return points
        finally:
            await db.close()

    async def create_invoice(self, user_id: int, inv_type: str, amount_myr: float, qty: int, bill_code: str, bill_url: str, expires_minutes: int, meta: Dict[str, Any] | None = None) -> int:
        now = utcnow()
        exp = now + timedelta(minutes=expires_minutes)
        db = await self.connect()
        try:
            cur = await db.execute(
                """
                INSERT INTO invoices (user_id, type, amount_myr, qty, bill_code, bill_url, status, created_at, expires_at, meta_json)
                VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?)
                """,
                (
                    user_id,
                    inv_type,
                    float(amount_myr),
                    int(qty),
                    bill_code,
                    bill_url,
                    dt_to_str(now),
                    dt_to_str(exp),
                    json.dumps(meta or {}),
                ),
            )
            await db.commit()
            return int(cur.lastrowid)
        finally:
            await db.close()

    async def get_invoice(self, invoice_id: int) -> Optional[dict]:
        db = await self.connect()
        try:
            cur = await db.execute("SELECT * FROM invoices WHERE id=?", (invoice_id,))
            row = await cur.fetchone()
            return dict(row) if row else None
        finally:
            await db.close()

    async def find_pending_invoice_by_billcode(self, bill_code: str) -> Optional[dict]:
        db = await self.connect()
        try:
            cur = await db.execute("SELECT * FROM invoices WHERE bill_code=? ORDER BY id DESC LIMIT 1", (bill_code,))
            row = await cur.fetchone()
            return dict(row) if row else None
        finally:
            await db.close()

    async def mark_invoice_paid(self, invoice_id: int) -> None:
        db = await self.connect()
        try:
            await db.execute("UPDATE invoices SET status='paid', paid_at=? WHERE id=?", (dt_to_str(utcnow()), invoice_id))
            await db.commit()
        finally:
            await db.close()

    async def mark_invoice_expired(self, invoice_id: int) -> None:
        db = await self.connect()
        try:
            await db.execute("UPDATE invoices SET status='expired' WHERE id=?", (invoice_id,))
            await db.commit()
        finally:
            await db.close()

    async def list_expired_unprocessed_invoices(self) -> list[dict]:
        """
        Pending invoices that are past expires_at.
        """
        db = await self.connect()
        try:
            cur = await db.execute(
                "SELECT * FROM invoices WHERE status='pending' AND expires_at < ?",
                (dt_to_str(utcnow()),),
            )
            rows = await cur.fetchall()
            return [dict(r) for r in rows]
        finally:
            await db.close()

    async def record_claim(self, user_id: int, protocol: str, days: int, channel: str, server_id: int | None, cost_credits: int, cost_vip: int, result: Dict[str, Any]) -> None:
        db = await self.connect()
        try:
            await db.execute(
                """
                INSERT INTO claims (user_id, protocol, days, channel, server_id, created_at, cost_credits, cost_vip_coins, result_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    protocol,
                    int(days),
                    channel,
                    server_id,
                    dt_to_str(utcnow()),
                    int(cost_credits),
                    int(cost_vip),
                    json.dumps(result),
                ),
            )
            await db.commit()
        finally:
            await db.close()

    async def count_claims_last_hour(self, channel: str) -> int:
        db = await self.connect()
        try:
            since = dt_to_str(utcnow() - timedelta(hours=1))
            cur = await db.execute("SELECT COUNT(*) AS c FROM claims WHERE channel=? AND created_at >= ?", (channel, since))
            row = await cur.fetchone()
            return int(row["c"]) if row else 0
        finally:
            await db.close()

    async def count_claimed_total(self, user_id: int) -> int:
        db = await self.connect()
        try:
            cur = await db.execute("SELECT COUNT(*) AS c FROM claims WHERE user_id=?", (user_id,))
            row = await cur.fetchone()
            return int(row["c"]) if row else 0
        finally:
            await db.close()

    async def add_server(self, pool: str, name: str, base_url: str, api_key: str, max_users: int = 100) -> int:
        db = await self.connect()
        try:
            cur = await db.execute(
                "INSERT INTO servers (pool, name, base_url, api_key, max_users, enabled) VALUES (?, ?, ?, ?, ?, 1)",
                (pool, name, base_url.rstrip("/"), api_key, int(max_users)),
            )
            await db.commit()
            return int(cur.lastrowid)
        finally:
            await db.close()

    async def list_servers(self, pool: str | None = None) -> list[dict]:
        db = await self.connect()
        try:
            if pool:
                cur = await db.execute("SELECT * FROM servers WHERE pool=? ORDER BY id ASC", (pool,))
            else:
                cur = await db.execute("SELECT * FROM servers ORDER BY id ASC")
            rows = await cur.fetchall()
            return [dict(r) for r in rows]
        finally:
            await db.close()

    async def set_server_enabled(self, server_id: int, enabled: bool) -> None:
        db = await self.connect()
        try:
            await db.execute("UPDATE servers SET enabled=? WHERE id=?", (1 if enabled else 0, server_id))
            await db.commit()
        finally:
            await db.close()

    async def set_server_notified_full(self, server_id: int, notified: bool) -> None:
        db = await self.connect()
        try:
            await db.execute("UPDATE servers SET last_notified_full=? WHERE id=?", (1 if notified else 0, server_id))
            await db.commit()
        finally:
            await db.close()

    async def support_map_add(self, admin_message_id: int, user_id: int) -> None:
        db = await self.connect()
        try:
            await db.execute(
                "INSERT INTO support_map (admin_message_id, user_id, created_at) VALUES (?, ?, ?)",
                (admin_message_id, user_id, dt_to_str(utcnow())),
            )
            await db.commit()
        finally:
            await db.close()

    async def support_map_get_user(self, admin_message_id: int) -> int | None:
        db = await self.connect()
        try:
            cur = await db.execute("SELECT user_id FROM support_map WHERE admin_message_id=? ORDER BY id DESC LIMIT 1", (admin_message_id,))
            row = await cur.fetchone()
            return int(row["user_id"]) if row else None
        finally:
            await db.close()
