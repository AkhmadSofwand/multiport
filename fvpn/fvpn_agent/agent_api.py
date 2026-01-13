\
from __future__ import annotations

import secrets
import string
from datetime import timedelta

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from .agent_db import AgentDB, dt_to_str, utcnow
from .config import AgentSettings, load_agent_settings
from .cleanup import cleanup_expired
from .ssh import create_ssh_user, generate_password, generate_username, user_exists
from .xray import create_trojan_user, create_vless_user, read_domain

app = FastAPI(title="FVPN Agent API")


class CreateRequest(BaseModel):
    protocol: str = Field(..., description="ssh | vless | trojan")
    days: int = Field(..., ge=1, le=365)


def get_settings() -> AgentSettings:
    return load_agent_settings()


async def verify_key(x_api_key: str | None = Header(default=None, alias="X-API-Key"), settings: AgentSettings = Depends(get_settings)):
    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="unauthorized")
    return True


@app.get("/health")
async def health(_: bool = Depends(verify_key)):
    return {"ok": True}


@app.get("/stats")
async def stats(_: bool = Depends(verify_key), settings: AgentSettings = Depends(get_settings)):
    # cleanup expired first, to keep active count accurate and enforce expiry.
    await cleanup_expired(settings)
    db = AgentDB(settings.db_path)
    await db.init()
    active = await db.count_active()
    return {"ok": True, "active_users": active, "max_users": settings.max_users}


@app.post("/create")
async def create(req: CreateRequest, _: bool = Depends(verify_key), settings: AgentSettings = Depends(get_settings)):
    protocol = req.protocol.lower().strip()
    days = int(req.days)

    # cleanup expired first
    await cleanup_expired(settings)

    db = AgentDB(settings.db_path)
    await db.init()
    active = await db.count_active()
    if active >= settings.max_users:
        return {"ok": False, "error": "server_full"}

    domain = read_domain(settings.domain_file)
    created_at = utcnow()
    expires_at = created_at + timedelta(days=days)

    if protocol == "ssh":
        # generate unique username
        username = generate_username(prefix="u", length=7)
        for _ in range(30):
            if not user_exists(username):
                break
            username = generate_username(prefix="u", length=7)
        password = generate_password(10)
        exp_dt = create_ssh_user(username, password, days)
        await db.add_account("ssh", username, password, dt_to_str(created_at), dt_to_str(exp_dt))
        return {
            "ok": True,
            "protocol": "ssh",
            "created_at": dt_to_str(created_at),
            "expires_at": exp_dt.date().isoformat(),
            "details": {"username": username, "password": password, "host": domain},
        }

    # For Xray-based protocols we generate a random username tag (email)
    username = "u" + secrets.token_hex(3)

    if protocol == "vless":
        uid, uri = create_vless_user(
            username=username,
            days=days,
            domain=domain,
            tls_port=settings.public_tls_port,
            ws_path=settings.vless_ws_path,
            vless_tls_config=settings.vless_tls_config,
            vless_none_config=settings.vless_none_config,
            restart_vless_service=settings.restart_vless_service,
            restart_none_service=settings.restart_vless_none_service,
        )
        await db.add_account("vless", username, uid, dt_to_str(created_at), dt_to_str(expires_at))
        return {
            "ok": True,
            "protocol": "vless",
            "created_at": dt_to_str(created_at),
            "expires_at": expires_at.date().isoformat(),
            "details": {"uri": uri},
        }

    if protocol == "trojan":
        pwd, uri = create_trojan_user(
            username=username,
            days=days,
            domain=domain,
            tls_port=settings.public_tls_port,
            ws_path=settings.trojan_ws_path,
            trojan_tls_config=settings.trojan_tls_config,
            restart_trojan_service=settings.restart_trojan_service,
        )
        await db.add_account("trojan", username, pwd, dt_to_str(created_at), dt_to_str(expires_at))
        return {
            "ok": True,
            "protocol": "trojan",
            "created_at": dt_to_str(created_at),
            "expires_at": expires_at.date().isoformat(),
            "details": {"uri": uri},
        }

    return {"ok": False, "error": "unsupported_protocol"}
