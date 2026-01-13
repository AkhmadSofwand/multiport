\
from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .config import Settings
from .i18n import t


def kb_subscription(settings: Settings, lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    # channel buttons
    for ch in settings.required_channels:
        url = f"https://t.me/{ch.lstrip('@')}"
        b.button(text=ch, url=url)
    b.adjust(1)
    b.button(text=t(lang, "btn_check_sub"), callback_data="act:check_sub")
    b.adjust(1)
    return b.as_markup()


def kb_agreement(settings: Settings, lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t(lang, "btn_read_agreement"), url=settings.user_agreement_url)
    b.button(text=t(lang, "btn_accept"), callback_data="act:accept_agreement")
    b.adjust(1)
    return b.as_markup()


def kb_main_menu(lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t(lang, "btn_verify"), callback_data="act:verify")
    b.button(text=t(lang, "btn_buy_vip"), callback_data="act:buy_vip")
    b.button(text=t(lang, "btn_profile"), callback_data="act:profile")
    b.button(text=t(lang, "btn_invite"), callback_data="act:invite")
    b.button(text=t(lang, "btn_convert"), callback_data="act:convert")
    b.button(text=t(lang, "btn_buy_star"), callback_data="act:buy_star")
    b.button(text=t(lang, "btn_checkin"), callback_data="act:checkin")
    b.button(text=t(lang, "btn_language"), callback_data="act:lang")
    b.button(text=t(lang, "btn_support"), callback_data="act:support")
    b.adjust(2, 2, 2, 2, 1)
    return b.as_markup()


def kb_back(lang: str, back_to: str = "act:menu") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t(lang, "btn_back"), callback_data=back_to)
    return b.as_markup()


def kb_verify_channels(lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🆓 Free", callback_data="verify:free")
    b.button(text="⚡ VIP", callback_data="verify:vip")
    b.button(text="⭐ Star", callback_data="verify:star")
    b.adjust(1)
    b.button(text=t(lang, "btn_back"), callback_data="act:menu")
    b.adjust(1)
    return b.as_markup()


def kb_protocols(lang: str, action: str, channel: str) -> InlineKeyboardMarkup:
    # action: claim|convert ; channel: free|vip|star|convert
    b = InlineKeyboardBuilder()
    b.button(text=f"🔐 {t(lang,'proto_ssh')}", callback_data=f"{action}:{channel}:ssh")
    b.button(text=f"🌀 {t(lang,'proto_vless')}", callback_data=f"{action}:{channel}:vless")
    b.button(text=f"🧿 {t(lang,'proto_trojan')}", callback_data=f"{action}:{channel}:trojan")
    b.adjust(1)
    b.button(text=t(lang, "btn_back"), callback_data="act:verify" if action == "claim" else "act:convert")
    b.adjust(1)
    return b.as_markup()


def kb_buy_vip(lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    packages = [
        (1, 1),
        (3, 2),
        (10, 5),
        (30, 10),
        (50, 15),
        (100, 25),
    ]
    for qty, myr in packages:
        b.button(text=f"{qty} coins = MYR{myr}", callback_data=f"buyvip:{qty}:{myr}")
    b.adjust(2, 2, 2)
    b.button(text=t(lang, "btn_back"), callback_data="act:menu")
    b.adjust(1)
    return b.as_markup()


def kb_buy_star(lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Pay MYR250", callback_data="buystar:250")
    b.button(text=t(lang, "btn_back"), callback_data="act:menu")
    b.adjust(1)
    return b.as_markup()


def kb_invoice(lang: str, invoice_id: int, bill_url: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="💳 Pay Now", url=bill_url)
    b.button(text="✅ Check Payment", callback_data=f"invcheck:{invoice_id}")
    b.adjust(1)
    b.button(text=t(lang, "btn_back"), callback_data="act:menu")
    b.adjust(1)
    return b.as_markup()


def kb_language(lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t(lang, "lang_ms"), callback_data="setlang:ms")
    b.button(text=t(lang, "lang_en"), callback_data="setlang:en")
    b.button(text=t(lang, "lang_zh"), callback_data="setlang:zh")
    b.adjust(1)
    b.button(text=t(lang, "btn_back"), callback_data="act:menu")
    b.adjust(1)
    return b.as_markup()


def kb_admin(lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="➕ Add Server", callback_data="admin:add_server")
    b.button(text="📋 List Servers", callback_data="admin:list_servers")
    b.button(text="🔒 Unblock User", callback_data="admin:unblock")
    b.adjust(1)
    b.button(text=t(lang, "btn_back"), callback_data="act:menu")
    b.adjust(1)
    return b.as_markup()
