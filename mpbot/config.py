import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict

DEFAULT_CONFIG_PATH = os.environ.get("MPBOT_CONFIG", "/etc/mpbot/config.json")


@dataclass
class ToyyibPayConfig:
    enabled: bool = False
    sandbox: bool = False
    secret_key: str = ""
    category_code: str = ""
    return_url: str = ""
    callback_url: str = ""


@dataclass
class BotConfig:
    token: str = ""
    admin_id: int = 0
    db_path: str = "/var/lib/mpbot/mpbot.db"
    toyyibpay: ToyyibPayConfig = ToyyibPayConfig()


def _deep_update(d: Dict[str, Any], u: Dict[str, Any]) -> Dict[str, Any]:
    for k, v in u.items():
        if isinstance(v, dict) and isinstance(d.get(k), dict):
            d[k] = _deep_update(d[k], v)
        else:
            d[k] = v
    return d


def load_config(path: str = DEFAULT_CONFIG_PATH) -> BotConfig:
    p = Path(path)
    if not p.exists():
        return BotConfig()
    data = json.loads(p.read_text(encoding="utf-8"))
    cfg = BotConfig()
    cfg.token = str(data.get("token", ""))
    cfg.admin_id = int(data.get("admin_id", 0))
    cfg.db_path = str(data.get("db_path", cfg.db_path))
    tp = data.get("toyyibpay", {}) or {}
    cfg.toyyibpay = ToyyibPayConfig(
        enabled=bool(tp.get("enabled", False)),
        sandbox=bool(tp.get("sandbox", False)),
        secret_key=str(tp.get("secret_key", "")),
        category_code=str(tp.get("category_code", "")),
        return_url=str(tp.get("return_url", "")),
        callback_url=str(tp.get("callback_url", "")),
    )
    return cfg


def save_config(cfg: BotConfig, path: str = DEFAULT_CONFIG_PATH) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    # Convert dataclasses to dict
    payload: Dict[str, Any] = {
        "token": cfg.token,
        "admin_id": cfg.admin_id,
        "db_path": cfg.db_path,
        "toyyibpay": asdict(cfg.toyyibpay),
    }

    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    os.chmod(tmp, 0o600)
    tmp.replace(p)


def update_config(patch: Dict[str, Any], path: str = DEFAULT_CONFIG_PATH) -> BotConfig:
    current = load_config(path)
    current_dict: Dict[str, Any] = {
        "token": current.token,
        "admin_id": current.admin_id,
        "db_path": current.db_path,
        "toyyibpay": asdict(current.toyyibpay),
    }
    merged = _deep_update(current_dict, patch)

    new_cfg = BotConfig()
    new_cfg.token = str(merged.get("token", ""))
    new_cfg.admin_id = int(merged.get("admin_id", 0))
    new_cfg.db_path = str(merged.get("db_path", current.db_path))
    tp = merged.get("toyyibpay", {}) or {}
    new_cfg.toyyibpay = ToyyibPayConfig(
        enabled=bool(tp.get("enabled", False)),
        sandbox=bool(tp.get("sandbox", False)),
        secret_key=str(tp.get("secret_key", "")),
        category_code=str(tp.get("category_code", "")),
        return_url=str(tp.get("return_url", "")),
        callback_url=str(tp.get("callback_url", "")),
    )
    save_config(new_cfg, path)
    return new_cfg
