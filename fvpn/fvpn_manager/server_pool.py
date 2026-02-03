from __future__ import annotations

import re
from typing import Any, Dict, Optional

import httpx

from .db import Database


class AgentError(Exception):
    pass


def _normalize_base_url(url: str) -> str:
    url = (url or "").strip().rstrip("/")
    if not url:
        return url
    if not re.match(r"^https?://", url, flags=re.I):
        url = "http://" + url
    return url


def _toggle_scheme(url: str) -> str:
    if url.lower().startswith("https://"):
        return "http://" + url[8:]
    if url.lower().startswith("http://"):
        return "https://" + url[7:]
    return url


async def _agent_get(base_url: str, path: str, secret: str, timeout: int = 8) -> Dict[str, Any]:
    """
    GET with scheme fallback (https<->http) for cases where user saved wrong scheme.
    """
    base_url = _normalize_base_url(base_url)
    headers = {"X-API-Key": secret}

    async def _do(u: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=timeout, verify=False) as client:
            r = await client.get(u + path, headers=headers)
            r.raise_for_status()
            return r.json()

    try:
        return await _do(base_url)
    except httpx.RequestError:
        alt = _toggle_scheme(base_url)
        if alt != base_url:
            return await _do(alt)
        raise


async def _agent_post(base_url: str, path: str, payload: Dict[str, Any], secret: str, timeout: int = 12) -> Dict[str, Any]:
    base_url = _normalize_base_url(base_url)
    headers = {"X-API-Key": secret}

    async def _do(u: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=timeout, verify=False) as client:
            r = await client.post(u + path, json=payload, headers=headers)
            r.raise_for_status()
            return r.json()

    try:
        return await _do(base_url)
    except httpx.RequestError:
        alt = _toggle_scheme(base_url)
        if alt != base_url:
            return await _do(alt)
        raise


async def select_server(db: Database, pool: str, bot=None, admin_chat_id: Optional[int] = None) -> Optional[dict]:
    """
    Pick an available server from DB:
    - enabled=1
    - pool matches
    - agent /stats reachable
    - active_users < max_users
    """
    pool = (pool or "").upper().strip()
    servers = await db.list_servers()
    candidates = [s for s in servers if int(s.get("enabled", 0)) == 1 and str(s.get("pool", "")).upper() == pool]

    for s in candidates:
        try:
            stats = await _agent_get(s["base_url"], "/stats", s["secret"])
            active = stats.get("active_users", stats.get("current_users", 0))
            active = int(active or 0)
            if active < int(s["max_users"]):
                return s
        except Exception:
            # unreachable or bad response -> skip
            continue

    # optional notify admin
    if bot and admin_chat_id:
        try:
            await bot.send_message(admin_chat_id, f"⚠️ No available server in pool={pool}. Please check agent connectivity.")
        except Exception:
            pass
    return None


async def create_vpn_account(db: Database, server_id: int, protocol: str, days: int) -> Dict[str, Any]:
    s = await db.get_server(server_id)
    if not s:
        raise AgentError("server_not_found")

    protocol = (protocol or "").lower().strip()
    if protocol not in {"ssh", "vless", "trojan"}:
        raise AgentError("unsupported_protocol")

    payload = {"protocol": protocol, "days": int(days)}
    try:
        res = await _agent_post(s["base_url"], "/create", payload, s["secret"])
        return res
    except httpx.HTTPStatusError as e:
        raise AgentError(f"agent_http_{e.response.status_code}") from e
    except Exception as e:
        raise AgentError("agent_unreachable") from e
