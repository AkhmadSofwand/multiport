\
from __future__ import annotations


def _normalize_base_url(base_url: str) -> str:
    base_url = (base_url or "").strip().rstrip("/")
    if base_url and not re.match(r"^https?://", base_url):
        base_url = "http://" + base_url
    return base_url

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

import httpx
from aiogram import Bot

from .db import Database


@dataclass
class AgentError(Exception):
    message: str


async def _agent_get(server: dict, path: str, timeout_sec: int) -> dict:
    url = server["base_url"].rstrip("/") + path
    headers = {"X-API-Key": server["api_key"]}
    async with httpx.AsyncClient(timeout=timeout_sec) as client:
        r = await client.get(url, headers=headers)
        r.raise_for_status()
        return r.json()


async def _agent_post(server: dict, path: str, payload: dict, timeout_sec: int) -> dict:
    url = server["base_url"].rstrip("/") + path
    headers = {"X-API-Key": server["api_key"]}
    async with httpx.AsyncClient(timeout=timeout_sec) as client:
        r = await client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        return r.json()


async def select_server(db: Database, pool: str, bot: Bot, admin_id: int, timeout_sec: int) -> Optional[dict]:
    pool = (pool or "").strip().upper()
    servers = await db.list_servers(pool)
    for s in servers:
        if int(s.get("enabled", 1)) != 1:
            continue
        try:
            stats = await _agent_get(s, "/stats", timeout_sec=timeout_sec)
            active = int(stats.get("active_users", 0))
            max_users = int(s.get("max_users", 100))
            if active < max_users:
                # reset full notification flag when back under cap
                if int(s.get("last_notified_full", 0)) == 1:
                    await db.set_server_notified_full(int(s["id"]), False)
                return s
            # full
            if int(s.get("last_notified_full", 0)) == 0:
                await db.set_server_notified_full(int(s["id"]), True)
                await bot.send_message(
                    admin_id,
                    f"⚠️ Server FULL: {s['name']} (pool={pool})\n"
                    f"Active users: {active}/{max_users}\n\n"
                    f"Please add a new server and register it in /admin.",
                )
        except Exception:
            # skip unreachable server (do not mark full)
            continue
    # no server available
    await bot.send_message(
        admin_id,
        f"🚨 No available server in pool={pool}. Users cannot claim right now.\n"
        f"Please add a new server and register it in /admin.",
    )
    return None


async def create_vpn_account(server: dict, protocol: str, days: int, timeout_sec: int) -> dict:
    protocol = protocol.lower()
    if protocol not in {"ssh", "vless", "trojan"}:
        raise AgentError("Unsupported protocol")

    try:
        res = await _agent_post(server, "/create", {"protocol": protocol, "days": int(days)}, timeout_sec=timeout_sec)
        if not res.get("ok"):
            raise AgentError(res.get("error", "Agent error"))
        return res
    except httpx.HTTPError as e:
        raise AgentError(f"Agent HTTP error: {e}")
    except Exception as e:
        # fallback: kalau user simpan https:// tapi agent sebenarnya http://, cuba sekali lagi guna http://
        if str(base_url).startswith("https://"):
            try:
                base_url_http = "http://" + str(base_url)[len("https://"):]
                async with httpx.AsyncClient(timeout=5) as client:
                    r = await client.post(f"{base_url_http}{path}", json=payload, headers={"x-agent-secret": secret})
                    r.raise_for_status()
                    return r.json()
            except Exception:
                pass
        # fallback: kalau user simpan https:// tapi agent sebenarnya http://, cuba sekali lagi guna http://
        if str(base_url).startswith("https://"):
            try:
                base_url_http = "http://" + str(base_url)[len("https://"):]
                async with httpx.AsyncClient(timeout=5) as client:
                    r = await client.get(f"{base_url_http}{path}", headers={"x-agent-secret": secret})
                    r.raise_for_status()
                    return r.json()
            except Exception:
                pass
        raise AgentError(f"Agent error: {e}")
