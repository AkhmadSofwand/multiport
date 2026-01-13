\
from __future__ import annotations

import os
from dataclasses import dataclass


def _getenv(name: str, default: str | None = None) -> str | None:
    v = os.getenv(name)
    if v is None or v == "":
        return default
    return v


def _getenv_int(name: str, default: int) -> int:
    v = _getenv(name)
    if v is None:
        return default
    try:
        return int(v)
    except ValueError:
        return default


@dataclass(frozen=True)
class AgentSettings:
    api_key: str
    listen_host: str
    listen_port: int
    max_users: int

    db_path: str

    # Domain/host info
    domain_file: str
    public_tls_port: int
    public_nontls_port: int

    # Xray config paths (multiport-compatible)
    vless_tls_config: str
    vless_none_config: str
    trojan_tls_config: str

    vless_ws_path: str
    trojan_ws_path: str

    # Systemd services to restart (optional)
    restart_vless_service: str
    restart_vless_none_service: str
    restart_trojan_service: str


def load_agent_settings() -> AgentSettings:
    api_key = _getenv("AGENT_API_KEY")
    if not api_key:
        raise RuntimeError("Missing AGENT_API_KEY")

    listen_host = _getenv("AGENT_LISTEN_HOST", "0.0.0.0") or "0.0.0.0"
    listen_port = _getenv_int("AGENT_LISTEN_PORT", 7000)
    max_users = _getenv_int("AGENT_MAX_USERS", 100)

    db_path = _getenv("AGENT_DB_PATH", "/var/lib/fvpn-agent/agent.db") or "/var/lib/fvpn-agent/agent.db"

    domain_file = _getenv("XRAY_DOMAIN_FILE", "/usr/local/etc/xray/domain") or "/usr/local/etc/xray/domain"
    public_tls_port = _getenv_int("PUBLIC_TLS_PORT", 443)
    public_nontls_port = _getenv_int("PUBLIC_NONTLS_PORT", 80)

    vless_tls_config = _getenv("XRAY_VLESS_TLS_CONFIG", "/usr/local/etc/xray/vless.json") or "/usr/local/etc/xray/vless.json"
    vless_none_config = _getenv("XRAY_VLESS_NONE_CONFIG", "/usr/local/etc/xray/vnone.json") or "/usr/local/etc/xray/vnone.json"
    trojan_tls_config = _getenv("XRAY_TROJAN_TLS_CONFIG", "/usr/local/etc/xray/trojanws.json") or "/usr/local/etc/xray/trojanws.json"

    vless_ws_path = _getenv("VLESS_WS_PATH", "/vless") or "/vless"
    trojan_ws_path = _getenv("TROJAN_WS_PATH", "/trojan") or "/trojan"

    restart_vless_service = _getenv("RESTART_VLESS_SERVICE", "xray@vless") or "xray@vless"
    restart_vless_none_service = _getenv("RESTART_VLESS_NONE_SERVICE", "xray@none") or "xray@none"
    restart_trojan_service = _getenv("RESTART_TROJAN_SERVICE", "xray@trojanws") or "xray@trojanws"

    return AgentSettings(
        api_key=api_key,
        listen_host=listen_host,
        listen_port=listen_port,
        max_users=max_users,
        db_path=db_path,
        domain_file=domain_file,
        public_tls_port=public_tls_port,
        public_nontls_port=public_nontls_port,
        vless_tls_config=vless_tls_config,
        vless_none_config=vless_none_config,
        trojan_tls_config=trojan_tls_config,
        vless_ws_path=vless_ws_path,
        trojan_ws_path=trojan_ws_path,
        restart_vless_service=restart_vless_service,
        restart_vless_none_service=restart_vless_none_service,
        restart_trojan_service=restart_trojan_service,
    )
