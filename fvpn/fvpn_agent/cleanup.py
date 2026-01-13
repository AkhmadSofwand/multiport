\
from __future__ import annotations

import os
import subprocess
from datetime import datetime, timezone
from typing import Tuple

from .agent_db import AgentDB
from .config import AgentSettings
from .xray import _restart_service  # internal helper


def _today_str() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _cleanup_config_file(path: str, username: str) -> bool:
    """
    Remove user block from multiport-style xray config:
    - line: ### username exp created uuid
    - next line: }},{"id":"...","email":"username"   OR  }},{"password":"...","email":"username"
    Returns True if file changed.
    """
    if not os.path.exists(path):
        return False
    changed = False
    out = []
    skip_next = False
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.read().splitlines()

    for i, line in enumerate(lines):
        if skip_next:
            skip_next = False
            changed = True
            continue
        if line.startswith("### "):
            parts = line.split()
            if len(parts) >= 3 and parts[1] == username:
                # remove this and the next line
                skip_next = True
                changed = True
                continue
        out.append(line)

    if changed:
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(out) + "\n")
    return changed


def _delete_ssh_user(username: str) -> None:
    try:
        subprocess.run(["userdel", "-r", username], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


async def cleanup_expired(settings: AgentSettings) -> dict:
    """
    Remove expired accounts that exist in AgentDB:
    - delete SSH system users
    - remove VLESS/Trojan blocks from config files
    - restart services if changed
    """
    db = AgentDB(settings.db_path)
    await db.init()

    expired = await db.list_expired()
    removed = 0
    changed_vless = False
    changed_vnone = False
    changed_trojan = False

    for acc in expired:
        protocol = acc["protocol"]
        username = acc["username"]
        if protocol == "ssh":
            _delete_ssh_user(username)
        elif protocol == "vless":
            changed_vless = _cleanup_config_file(settings.vless_tls_config, username) or changed_vless
            changed_vnone = _cleanup_config_file(settings.vless_none_config, username) or changed_vnone
        elif protocol == "trojan":
            changed_trojan = _cleanup_config_file(settings.trojan_tls_config, username) or changed_trojan

        await db.delete_account(int(acc["id"]))
        removed += 1

    # restart services only when modified
    if changed_vless:
        _restart_service(settings.restart_vless_service)
    if changed_vnone:
        _restart_service(settings.restart_vless_none_service)
    if changed_trojan:
        _restart_service(settings.restart_trojan_service)

    return {"removed": removed}
