\
from __future__ import annotations

import os
import re
import subprocess
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def read_domain(domain_file: str) -> str:
    for p in [domain_file, "/etc/xray/domain", "/root/domain"]:
        try:
            if os.path.exists(p):
                d = open(p, "r", encoding="utf-8").read().strip()
                if d:
                    return d
        except Exception:
            continue
    # fallback: public IP (best effort)
    try:
        ip = subprocess.check_output(["bash", "-lc", "curl -s ifconfig.me || curl -s ipinfo.io/ip || hostname -I | awk '{print $1}'"]).decode().strip()
        return ip or "127.0.0.1"
    except Exception:
        return "127.0.0.1"


def new_uuid() -> str:
    return str(uuid.uuid4())


def _insert_after_marker(path: str, marker_regex: str, insert_lines: list[str]) -> None:
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.read().splitlines()

    out: list[str] = []
    inserted = False
    rx = re.compile(marker_regex)
    for line in lines:
        out.append(line)
        if (not inserted) and rx.search(line):
            # insert after marker line
            out.extend(insert_lines)
            inserted = True

    if not inserted:
        raise RuntimeError(f"Marker not found in {path}: {marker_regex}")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


def _restart_service(service: str) -> None:
    # Try restart service; ignore if not exist
    try:
        subprocess.run(["systemctl", "restart", service], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        try:
            subprocess.run(["systemctl", "restart", "xray"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass


def create_vless_user(
    username: str,
    days: int,
    domain: str,
    tls_port: int,
    ws_path: str,
    vless_tls_config: str,
    vless_none_config: str,
    restart_vless_service: str,
    restart_none_service: str,
) -> Tuple[str, str]:
    """
    Returns (uuid, vless_uri)
    Compatible with multiport config insertion (markers #tls / #none).
    """
    uid = new_uuid()
    exp_date = (utcnow() + timedelta(days=days)).date().isoformat()
    created_date = utcnow().date().isoformat()

    # Insert into TLS config
    insert_lines_tls = [
        f"### {username} {exp_date} {created_date} {uid}",
        f'}},{{"id":"{uid}","email":"{username}"',
    ]
    _insert_after_marker(vless_tls_config, r"#tls\s*$", insert_lines_tls)
    _restart_service(restart_vless_service)

    # Insert into NONE config if exists
    if os.path.exists(vless_none_config):
        insert_lines_none = [
            f"### {username} {exp_date} {created_date} {uid}",
            f'}},{{"id":"{uid}","email":"{username}"',
        ]
        try:
            _insert_after_marker(vless_none_config, r"#none\s*$", insert_lines_none)
            _restart_service(restart_none_service)
        except Exception:
            pass

    # Build TLS WS URI (link only)
    # Standard format:
    # vless://UUID@domain:443?type=ws&encryption=none&security=tls&sni=domain&host=domain&path=/vless#username
    uri = (
        f"vless://{uid}@{domain}:{tls_port}"
        f"?type=ws&encryption=none&security=tls&sni={domain}&host={domain}&path={ws_path}"
        f"#{username}"
    )
    return uid, uri


def create_trojan_user(
    username: str,
    days: int,
    domain: str,
    tls_port: int,
    ws_path: str,
    trojan_tls_config: str,
    restart_trojan_service: str,
) -> Tuple[str, str]:
    """
    Returns (password, trojan_uri)
    Compatible with multiport config insertion (marker #tls).
    """
    pwd = new_uuid()
    exp_date = (utcnow() + timedelta(days=days)).date().isoformat()
    created_date = utcnow().date().isoformat()

    insert_lines = [
        f"### {username} {exp_date} {created_date} {pwd}",
        f'}},{{"password":"{pwd}","level":0,"email":"{username}"',
    ]
    _insert_after_marker(trojan_tls_config, r"#tls\s*$", insert_lines)
    _restart_service(restart_trojan_service)

    # trojan ws tls URI
    uri = (
        f"trojan://{pwd}@{domain}:{tls_port}"
        f"?type=ws&security=tls&sni={domain}&host={domain}&path={ws_path}"
        f"#{username}"
    )
    return pwd, uri
