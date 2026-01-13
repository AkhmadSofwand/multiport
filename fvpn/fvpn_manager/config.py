\
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List


def _getenv(name: str, default: str | None = None) -> str | None:
    v = os.getenv(name)
    if v is None or v == "":
        return default
    return v


def _getenv_int(name: str, default: int) -> int:
    v = _getenv(name, None)
    if v is None:
        return default
    try:
        return int(v)
    except ValueError:
        return default


def _getenv_bool(name: str, default: bool = False) -> bool:
    v = _getenv(name, None)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class Settings:
    # Telegram
    main_bot_token: str
    support_bot_token: str | None
    admin_id: int
    bot_username: str

    required_channels: List[str]  # usernames with @ or without

    # User agreement
    user_agreement_url: str

    # Limits & pricing
    free_slots_per_hour: int
    free_claim_cost_credits: int
    free_claim_validity_days: int

    convert_cost_credits: int
    convert_validity_days: int

    vip_claim_cost_vip_coins: int
    vip_claim_validity_days: int

    star_subscription_days: int

    # Payments (ToyyibPay)
    toyyibpay_enabled: bool
    toyyibpay_is_sandbox: bool
    toyyibpay_user_secret_key: str
    toyyibpay_category_code: str
    toyyibpay_return_url: str
    toyyibpay_callback_url: str
    invoice_expire_minutes: int

    # Database
    db_path: str

    # HTTP
    agent_timeout_sec: int
    server_ping_timeout_sec: int


def load_settings() -> Settings:
    main_bot_token = _getenv("MAIN_BOT_TOKEN")
    if not main_bot_token:
        raise RuntimeError("Missing MAIN_BOT_TOKEN")

    support_bot_token = _getenv("SUPPORT_BOT_TOKEN", None)

    admin_id_str = _getenv("ADMIN_ID")
    if not admin_id_str:
        raise RuntimeError("Missing ADMIN_ID")
    admin_id = int(admin_id_str)

    bot_username = (_getenv("BOT_USERNAME", "fvpngenebot") or "fvpngenebot").lstrip("@")

    # Channels: comma separated
    channels_raw = _getenv("REQUIRED_CHANNELS", "@connectifyvpninfo,@connectifyvpnstore") or ""
    required_channels = []
    for c in channels_raw.split(","):
        c = c.strip()
        if not c:
            continue
        required_channels.append(c if c.startswith("@") else f"@{c}")

    user_agreement_url = _getenv("USER_AGREEMENT_URL", "https://telegra.ph/") or "https://telegra.ph/"

    # Limits
    free_slots_per_hour = _getenv_int("FREE_SLOTS_PER_HOUR", 20)
    free_claim_cost_credits = _getenv_int("FREE_CLAIM_COST_CREDITS", 1)
    free_claim_validity_days = _getenv_int("FREE_CLAIM_VALIDITY_DAYS", 3)

    convert_cost_credits = _getenv_int("CONVERT_COST_CREDITS", 10)
    convert_validity_days = _getenv_int("CONVERT_VALIDITY_DAYS", 30)

    vip_claim_cost_vip_coins = _getenv_int("VIP_CLAIM_COST_VIP_COINS", 1)
    vip_claim_validity_days = _getenv_int("VIP_CLAIM_VALIDITY_DAYS", 3)

    star_subscription_days = _getenv_int("STAR_SUBSCRIPTION_DAYS", 30)

    # Payments
    toyyibpay_enabled = _getenv_bool("TOYYIBPAY_ENABLED", True)
    toyyibpay_is_sandbox = _getenv_bool("TOYYIBPAY_IS_SANDBOX", False)
    toyyibpay_user_secret_key = _getenv("TOYYIBPAY_USER_SECRET_KEY", "") or ""
    toyyibpay_category_code = _getenv("TOYYIBPAY_CATEGORY_CODE", "") or ""
    toyyibpay_return_url = _getenv("TOYYIBPAY_RETURN_URL", "https://t.me/" + bot_username) or ""
    toyyibpay_callback_url = _getenv("TOYYIBPAY_CALLBACK_URL", "") or ""  # optional
    invoice_expire_minutes = _getenv_int("INVOICE_EXPIRE_MINUTES", 60)

    db_path = _getenv("DB_PATH", "/var/lib/fvpn-manager/manager.db") or "/var/lib/fvpn-manager/manager.db"

    agent_timeout_sec = _getenv_int("AGENT_TIMEOUT_SEC", 15)
    server_ping_timeout_sec = _getenv_int("SERVER_PING_TIMEOUT_SEC", 5)

    return Settings(
        main_bot_token=main_bot_token,
        support_bot_token=support_bot_token,
        admin_id=admin_id,
        bot_username=bot_username,
        required_channels=required_channels,
        user_agreement_url=user_agreement_url,
        free_slots_per_hour=free_slots_per_hour,
        free_claim_cost_credits=free_claim_cost_credits,
        free_claim_validity_days=free_claim_validity_days,
        convert_cost_credits=convert_cost_credits,
        convert_validity_days=convert_validity_days,
        vip_claim_cost_vip_coins=vip_claim_cost_vip_coins,
        vip_claim_validity_days=vip_claim_validity_days,
        star_subscription_days=star_subscription_days,
        toyyibpay_enabled=toyyibpay_enabled,
        toyyibpay_is_sandbox=toyyibpay_is_sandbox,
        toyyibpay_user_secret_key=toyyibpay_user_secret_key,
        toyyibpay_category_code=toyyibpay_category_code,
        toyyibpay_return_url=toyyibpay_return_url,
        toyyibpay_callback_url=toyyibpay_callback_url,
        invoice_expire_minutes=invoice_expire_minutes,
        db_path=db_path,
        agent_timeout_sec=agent_timeout_sec,
        server_ping_timeout_sec=server_ping_timeout_sec,
    )
