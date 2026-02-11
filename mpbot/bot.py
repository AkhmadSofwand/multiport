import asyncio
import json
import os
import re
import subprocess
from dataclasses import asdict
from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    ConversationHandler,
    filters,
)

from .config import DEFAULT_CONFIG_PATH, load_config, update_config
from .db import DB
from .ops import OpsError, create_ssh, create_vmess, create_vless, create_trojan, renew_account
from .toyyibpay import create_bill, ToyyibPayError

# Conversation states
(
    ST_SSH_USER,
    ST_SSH_PASS,
    ST_SSH_DAYS,
    ST_VMESS_USER,
    ST_VMESS_BUG,
    ST_VMESS_SNI,
    ST_VMESS_DAYS,
    ST_VLESS_USER,
    ST_VLESS_BUG,
    ST_VLESS_SNI,
    ST_VLESS_DAYS,
    ST_TROJAN_USER,
    ST_TROJAN_PASS,
    ST_TROJAN_BUG,
    ST_TROJAN_SNI,
    ST_TROJAN_DAYS,
    ST_RENEW_PROTO,
    ST_RENEW_USER,
    ST_RENEW_DAYS,
) = range(18)


def is_admin(cfg, uid: int) -> bool:
    return int(uid) == int(cfg.admin_id)


def money(cents: int) -> str:
    return f"RM{cents/100:.2f}"


def main_menu_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("🧩 SSH", callback_data="m:ssh"), InlineKeyboardButton("⚡ VMESS", callback_data="m:vmess")],
        [InlineKeyboardButton("🛰 VLESS", callback_data="m:vless"), InlineKeyboardButton("🛡 TROJAN", callback_data="m:trojan")],
        [InlineKeyboardButton("♻️ Renew", callback_data="m:renew"), InlineKeyboardButton("👥 Accounts", callback_data="m:accounts")],
        [InlineKeyboardButton("💳 Topup", callback_data="m:topup")],
    ]
    return InlineKeyboardMarkup(rows)


def topup_kb() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton("RM10", callback_data="t:1000"),
            InlineKeyboardButton("RM20", callback_data="t:2000"),
            InlineKeyboardButton("RM30", callback_data="t:3000"),
        ],
        [
            InlineKeyboardButton("RM50", callback_data="t:5000"),
            InlineKeyboardButton("RM100", callback_data="t:10000"),
        ],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="m:home")],
    ]
    return InlineKeyboardMarkup(rows)


def renew_proto_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("SSH", callback_data="r:SSH"), InlineKeyboardButton("VMESS", callback_data="r:VMESS"), InlineKeyboardButton("VLESS", callback_data="r:VLESS")],
        [InlineKeyboardButton("TROJAN", callback_data="r:TROJAN")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="m:home")],
    ]
    return InlineKeyboardMarkup(rows)


WELCOME = (
    "<b>Panel VPN Multiport</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "Gunakan butang di bawah untuk urus akaun.\n"
    "\n"
    "<i>Nota:</i> Sistem ini jalankan command terus dalam VPS.\n"
)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cfg = load_config(DEFAULT_CONFIG_PATH)
    db = DB(cfg.db_path)

    user = update.effective_user
    db.upsert_user(user.id, user.username or user.full_name)
    u = db.get_user(user.id)
    bal = u.balance_cents if u else 0

    text = WELCOME + f"\n<b>Baki:</b> {money(bal)}\n"
    await update.message.reply_text(text, reply_markup=main_menu_kb(), parse_mode=ParseMode.HTML)


async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await cmd_start(update, context)


async def go_home(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    cfg = load_config(DEFAULT_CONFIG_PATH)
    db = DB(cfg.db_path)
    user = query.from_user
    db.upsert_user(user.id, user.username or user.full_name)
    u = db.get_user(user.id)
    bal = u.balance_cents if u else 0
    text = WELCOME + f"\n<b>Baki:</b> {money(bal)}\n"
    await query.edit_message_text(text, reply_markup=main_menu_kb(), parse_mode=ParseMode.HTML)


async def show_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    cfg = load_config(DEFAULT_CONFIG_PATH)
    db = DB(cfg.db_path)
    user = query.from_user
    db.upsert_user(user.id, user.username or user.full_name)
    accounts = db.list_accounts(user.id)

    if not accounts:
        msg = "Tiada akaun dalam rekod bot lagi.\n\n(Nota: akaun yang dibuat manual di luar bot tidak dipaparkan di sini.)"
    else:
        lines = ["<b>Accounts</b>", "━━━━━━━━━━━━━━━━━━━━━━"]
        for a in accounts:
            exp = a.get("expires_at") or "-"
            lines.append(f"• <b>{a['protocol']}</b> — <code>{a['username']}</code> (exp: {exp})")
        msg = "\n".join(lines)

    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="m:home")]]), parse_mode=ParseMode.HTML)


async def show_topup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    cfg = load_config(DEFAULT_CONFIG_PATH)
    db = DB(cfg.db_path)
    user = query.from_user
    db.upsert_user(user.id, user.username or user.full_name)
    u = db.get_user(user.id)
    bal = u.balance_cents if u else 0

    text = (
        "<b>Topup Baki</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Baki semasa: <b>{money(bal)}</b>\n\n"
        "Pilih jumlah topup:" 
    )
    await query.edit_message_text(text, reply_markup=topup_kb(), parse_mode=ParseMode.HTML)


async def do_topup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    cfg = load_config(DEFAULT_CONFIG_PATH)
    db = DB(cfg.db_path)
    user = query.from_user
    db.upsert_user(user.id, user.username or user.full_name)

    if not cfg.toyyibpay.enabled:
        await query.edit_message_text(
            "Topup belum diaktifkan. Sila hubungi admin.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="m:home")]]),
        )
        return

    amount_cents = int(query.data.split(":", 1)[1])
    ref = f"tg_{user.id}_{int(asyncio.get_running_loop().time())}"

    # Create bill
    try:
        result = await create_bill(
            sandbox=cfg.toyyibpay.sandbox,
            secret_key=cfg.toyyibpay.secret_key,
            category_code=cfg.toyyibpay.category_code,
            bill_name="Topup Panel VPN",
            bill_desc=f"Topup baki {money(amount_cents)}",
            amount_cents=amount_cents,
            payer_name=user.full_name or "User",
            payer_email=f"user{user.id}@example.local",
            payer_phone="0000000000",
            return_url=cfg.toyyibpay.return_url,
            callback_url=cfg.toyyibpay.callback_url,
            reference_1=ref,
        )
    except ToyyibPayError as e:
        await query.edit_message_text(
            f"ToyyibPay error: {e}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="m:topup")]]),
        )
        return

    db.create_topup(user.id, result.bill_code, amount_cents)

    msg = (
        "<b>Link Pembayaran</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Jumlah: <b>{money(amount_cents)}</b>\n"
        f"BillCode: <code>{result.bill_code}</code>\n\n"
        "Klik link di bawah untuk bayar:\n"
        f"{result.payment_url}\n\n"
        "Selepas berjaya, baki akan masuk automatik (callback)."
    )
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="m:home")]]), parse_mode=ParseMode.HTML)


async def menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    data = query.data
    if data == "m:home":
        await go_home(update, context)
        return ConversationHandler.END
    if data == "m:accounts":
        await show_accounts(update, context)
        return ConversationHandler.END
    if data == "m:topup":
        await show_topup(update, context)
        return ConversationHandler.END
    if data.startswith("t:"):
        await do_topup(update, context)
        return ConversationHandler.END

    if data == "m:ssh":
        await query.edit_message_text("Masukkan <b>username SSH</b>:", parse_mode=ParseMode.HTML)
        return ST_SSH_USER
    if data == "m:vmess":
        await query.edit_message_text("Masukkan <b>username VMESS</b>:", parse_mode=ParseMode.HTML)
        return ST_VMESS_USER
    if data == "m:vless":
        await query.edit_message_text("Masukkan <b>username VLESS</b>:", parse_mode=ParseMode.HTML)
        return ST_VLESS_USER
    if data == "m:trojan":
        await query.edit_message_text("Masukkan <b>username TROJAN</b>:", parse_mode=ParseMode.HTML)
        return ST_TROJAN_USER
    if data == "m:renew":
        await query.edit_message_text("Pilih protokol untuk renew:", reply_markup=renew_proto_kb())
        return ST_RENEW_PROTO

    # fallback
    await go_home(update, context)
    return ConversationHandler.END


def _valid_user(s: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9_]{3,32}", s.strip()))


def _valid_days(s: str) -> Optional[int]:
    s = s.strip()
    if not re.fullmatch(r"\d{1,4}", s):
        return None
    v = int(s)
    return v if v > 0 else None


async def ssh_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    t = update.message.text.strip()
    if not _valid_user(t):
        await update.message.reply_text("Username tidak sah. Cuba lagi:")
        return ST_SSH_USER
    context.user_data["ssh_user"] = t
    await update.message.reply_text("Masukkan <b>password SSH</b>:", parse_mode=ParseMode.HTML)
    return ST_SSH_PASS


async def ssh_pass(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["ssh_pass"] = update.message.text.strip()
    await update.message.reply_text("Masukkan tempoh <b>Expired (hari)</b>:", parse_mode=ParseMode.HTML)
    return ST_SSH_DAYS


async def ssh_days(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    days = _valid_days(update.message.text)
    if not days:
        await update.message.reply_text("Days tidak sah. Masukkan nombor (contoh: 30):")
        return ST_SSH_DAYS

    cfg = load_config(DEFAULT_CONFIG_PATH)
    db = DB(cfg.db_path)
    user = update.effective_user
    db.upsert_user(user.id, user.username or user.full_name)

    u = context.user_data["ssh_user"]
    p = context.user_data["ssh_pass"]

    try:
        out = await asyncio.to_thread(create_ssh, u, p, days)
    except OpsError as e:
        await update.message.reply_text(f"Gagal create SSH:\n<pre>{str(e)}</pre>", parse_mode=ParseMode.HTML)
        return ConversationHandler.END

    db.add_account(user.id, "SSH", u, p, None, meta=out[-2000:])
    await update.message.reply_text(f"Berjaya create SSH.\n\n<pre>{out[-2000:]}</pre>", parse_mode=ParseMode.HTML)
    await update.message.reply_text("Menu:", reply_markup=main_menu_kb())
    return ConversationHandler.END


async def vmess_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    t = update.message.text.strip()
    if not _valid_user(t):
        await update.message.reply_text("Username tidak sah. Cuba lagi:")
        return ST_VMESS_USER
    context.user_data["vmess_user"] = t
    await update.message.reply_text("Bug Address (optional, boleh kosong):")
    return ST_VMESS_BUG


async def vmess_bug(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["vmess_bug"] = update.message.text.strip()
    await update.message.reply_text("SNI/Host (optional, boleh kosong):")
    return ST_VMESS_SNI


async def vmess_sni(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["vmess_sni"] = update.message.text.strip()
    await update.message.reply_text("Expired (hari):")
    return ST_VMESS_DAYS


async def vmess_days(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    days = _valid_days(update.message.text)
    if not days:
        await update.message.reply_text("Days tidak sah. Masukkan nombor:")
        return ST_VMESS_DAYS

    cfg = load_config(DEFAULT_CONFIG_PATH)
    db = DB(cfg.db_path)
    user = update.effective_user
    db.upsert_user(user.id, user.username or user.full_name)

    u = context.user_data["vmess_user"]
    bug = context.user_data.get("vmess_bug", "")
    sni = context.user_data.get("vmess_sni", "")

    try:
        out = await asyncio.to_thread(create_vmess, u, bug, sni, days)
    except OpsError as e:
        await update.message.reply_text(f"Gagal create VMESS:\n<pre>{str(e)}</pre>", parse_mode=ParseMode.HTML)
        return ConversationHandler.END

    db.add_account(user.id, "VMESS", u, None, None, meta=out[-2000:])
    await update.message.reply_text(f"Berjaya create VMESS.\n\n<pre>{out[-2000:]}</pre>", parse_mode=ParseMode.HTML)
    await update.message.reply_text("Menu:", reply_markup=main_menu_kb())
    return ConversationHandler.END


async def vless_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    t = update.message.text.strip()
    if not _valid_user(t):
        await update.message.reply_text("Username tidak sah. Cuba lagi:")
        return ST_VLESS_USER
    context.user_data["vless_user"] = t
    await update.message.reply_text("Bug Address (optional, boleh kosong):")
    return ST_VLESS_BUG


async def vless_bug(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["vless_bug"] = update.message.text.strip()
    await update.message.reply_text("SNI/Host (optional, boleh kosong):")
    return ST_VLESS_SNI


async def vless_sni(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["vless_sni"] = update.message.text.strip()
    await update.message.reply_text("Expired (hari):")
    return ST_VLESS_DAYS


async def vless_days(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    days = _valid_days(update.message.text)
    if not days:
        await update.message.reply_text("Days tidak sah. Masukkan nombor:")
        return ST_VLESS_DAYS

    cfg = load_config(DEFAULT_CONFIG_PATH)
    db = DB(cfg.db_path)
    user = update.effective_user
    db.upsert_user(user.id, user.username or user.full_name)

    u = context.user_data["vless_user"]
    bug = context.user_data.get("vless_bug", "")
    sni = context.user_data.get("vless_sni", "")

    try:
        out = await asyncio.to_thread(create_vless, u, bug, sni, days)
    except OpsError as e:
        await update.message.reply_text(f"Gagal create VLESS:\n<pre>{str(e)}</pre>", parse_mode=ParseMode.HTML)
        return ConversationHandler.END

    db.add_account(user.id, "VLESS", u, None, None, meta=out[-2000:])
    await update.message.reply_text(f"Berjaya create VLESS.\n\n<pre>{out[-2000:]}</pre>", parse_mode=ParseMode.HTML)
    await update.message.reply_text("Menu:", reply_markup=main_menu_kb())
    return ConversationHandler.END


async def trojan_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    t = update.message.text.strip()
    if not _valid_user(t):
        await update.message.reply_text("Username tidak sah. Cuba lagi:")
        return ST_TROJAN_USER
    context.user_data["trojan_user"] = t
    await update.message.reply_text("Masukkan password trojan:")
    return ST_TROJAN_PASS


async def trojan_pass(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["trojan_pass"] = update.message.text.strip()
    await update.message.reply_text("Bug Address (optional, boleh kosong):")
    return ST_TROJAN_BUG


async def trojan_bug(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["trojan_bug"] = update.message.text.strip()
    await update.message.reply_text("SNI/Host (optional, boleh kosong):")
    return ST_TROJAN_SNI


async def trojan_sni(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["trojan_sni"] = update.message.text.strip()
    await update.message.reply_text("Expired (hari):")
    return ST_TROJAN_DAYS


async def trojan_days(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    days = _valid_days(update.message.text)
    if not days:
        await update.message.reply_text("Days tidak sah. Masukkan nombor:")
        return ST_TROJAN_DAYS

    cfg = load_config(DEFAULT_CONFIG_PATH)
    db = DB(cfg.db_path)
    user = update.effective_user
    db.upsert_user(user.id, user.username or user.full_name)

    u = context.user_data["trojan_user"]
    p = context.user_data["trojan_pass"]
    bug = context.user_data.get("trojan_bug", "")
    sni = context.user_data.get("trojan_sni", "")

    try:
        out = await asyncio.to_thread(create_trojan, u, p, bug, sni, days)
    except OpsError as e:
        await update.message.reply_text(f"Gagal create TROJAN:\n<pre>{str(e)}</pre>", parse_mode=ParseMode.HTML)
        return ConversationHandler.END

    db.add_account(user.id, "TROJAN", u, p, None, meta=out[-2000:])
    await update.message.reply_text(f"Berjaya create TROJAN.\n\n<pre>{out[-2000:]}</pre>", parse_mode=ParseMode.HTML)
    await update.message.reply_text("Menu:", reply_markup=main_menu_kb())
    return ConversationHandler.END


async def renew_select_proto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    proto = query.data.split(":", 1)[1]
    context.user_data["renew_proto"] = proto
    await query.edit_message_text(f"Masukkan username untuk renew ({proto}):")
    return ST_RENEW_USER


async def renew_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    t = update.message.text.strip()
    if not _valid_user(t):
        await update.message.reply_text("Username tidak sah. Cuba lagi:")
        return ST_RENEW_USER
    context.user_data["renew_user"] = t
    await update.message.reply_text("Extend berapa hari?")
    return ST_RENEW_DAYS


async def renew_days(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    days = _valid_days(update.message.text)
    if not days:
        await update.message.reply_text("Days tidak sah. Masukkan nombor:")
        return ST_RENEW_DAYS

    cfg = load_config(DEFAULT_CONFIG_PATH)
    db = DB(cfg.db_path)
    user = update.effective_user
    db.upsert_user(user.id, user.username or user.full_name)

    proto = context.user_data["renew_proto"]
    uname = context.user_data["renew_user"]

    try:
        out = await asyncio.to_thread(renew_account, proto, uname, days)
    except OpsError as e:
        await update.message.reply_text(f"Gagal renew:\n<pre>{str(e)}</pre>", parse_mode=ParseMode.HTML)
        return ConversationHandler.END

    await update.message.reply_text(f"Berjaya renew {proto}.\n\n<pre>{out[-2000:]}</pre>", parse_mode=ParseMode.HTML)
    await update.message.reply_text("Menu:", reply_markup=main_menu_kb())
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Dibatalkan.", reply_markup=main_menu_kb())
    return ConversationHandler.END


async def cmd_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cfg = load_config(DEFAULT_CONFIG_PATH)
    db = DB(cfg.db_path)
    user = update.effective_user
    db.upsert_user(user.id, user.username or user.full_name)
    u = db.get_user(user.id)
    bal = u.balance_cents if u else 0
    await update.message.reply_text(f"Baki anda: {money(bal)}", reply_markup=main_menu_kb())


# ---------------- Admin ToyyibPay commands ----------------

def _admin_only(update: Update, cfg) -> bool:
    uid = update.effective_user.id
    if not is_admin(cfg, uid):
        return False
    return True


def _restart_services() -> None:
    # Restart bot + api service. This function is called from inside bot; it will restart itself.
    for svc in ("mpbot", "mpbot-api"):
        subprocess.run(["systemctl", "restart", f"{svc}.service"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


async def toyyib_show(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cfg = load_config(DEFAULT_CONFIG_PATH)
    if not _admin_only(update, cfg):
        return
    tp = cfg.toyyibpay
    msg = (
        "💳 <b>ToyyibPay Config</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Enabled  : <b>{tp.enabled}</b>\n"
        f"Sandbox  : <b>{tp.sandbox}</b>\n"
        f"SecretKey: <code>{tp.secret_key[:4]}...{tp.secret_key[-4:] if tp.secret_key else ''}</code>\n"
        f"Category : <code>{tp.category_code}</code>\n"
        f"ReturnURL: <code>{tp.return_url}</code>\n"
        f"Callback : <code>{tp.callback_url}</code>\n"
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)


async def toyyib_enable(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cfg = load_config(DEFAULT_CONFIG_PATH)
    if not _admin_only(update, cfg):
        return
    if not context.args:
        await update.message.reply_text("Guna: /toyyib_enable true|false")
        return
    val = context.args[0].lower() == "true"
    update_config({"toyyibpay": {"enabled": val}}, DEFAULT_CONFIG_PATH)
    await update.message.reply_text("✅ Updated. Restarting service...")
    _restart_services()


async def toyyib_sandbox(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cfg = load_config(DEFAULT_CONFIG_PATH)
    if not _admin_only(update, cfg):
        return
    if not context.args:
        await update.message.reply_text("Guna: /toyyib_sandbox true|false")
        return
    val = context.args[0].lower() == "true"
    update_config({"toyyibpay": {"sandbox": val}}, DEFAULT_CONFIG_PATH)
    await update.message.reply_text("✅ Updated. Restarting service...")
    _restart_services()


async def toyyib_setkey(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cfg = load_config(DEFAULT_CONFIG_PATH)
    if not _admin_only(update, cfg):
        return
    if not context.args:
        await update.message.reply_text("Guna: /toyyib_setkey <USER_SECRET_KEY>")
        return
    key = context.args[0].strip()
    update_config({"toyyibpay": {"secret_key": key}}, DEFAULT_CONFIG_PATH)
    await update.message.reply_text("✅ Secret Key disimpan. Restarting service...")
    _restart_services()


async def toyyib_setcat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cfg = load_config(DEFAULT_CONFIG_PATH)
    if not _admin_only(update, cfg):
        return
    if not context.args:
        await update.message.reply_text("Guna: /toyyib_setcat <CATEGORY_CODE>")
        return
    code = context.args[0].strip()
    update_config({"toyyibpay": {"category_code": code}}, DEFAULT_CONFIG_PATH)
    await update.message.reply_text("✅ Category Code disimpan. Restarting service...")
    _restart_services()


async def toyyib_setreturn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cfg = load_config(DEFAULT_CONFIG_PATH)
    if not _admin_only(update, cfg):
        return
    if not context.args:
        await update.message.reply_text("Guna: /toyyib_setreturn <URL>")
        return
    url = context.args[0].strip()
    update_config({"toyyibpay": {"return_url": url}}, DEFAULT_CONFIG_PATH)
    await update.message.reply_text("✅ Return URL disimpan. Restarting service...")
    _restart_services()


async def toyyib_setcallback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cfg = load_config(DEFAULT_CONFIG_PATH)
    if not _admin_only(update, cfg):
        return
    if not context.args:
        await update.message.reply_text("Guna: /toyyib_setcallback <URL>|empty")
        return
    if context.args[0].lower() == "empty":
        url = ""
    else:
        url = context.args[0].strip()
    update_config({"toyyibpay": {"callback_url": url}}, DEFAULT_CONFIG_PATH)
    await update.message.reply_text("✅ Callback URL disimpan. Restarting service...")
    _restart_services()


async def toyyib_restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cfg = load_config(DEFAULT_CONFIG_PATH)
    if not _admin_only(update, cfg):
        return
    await update.message.reply_text("♻️ Restarting bot service...")
    _restart_services()


def build_app(token: str) -> Application:
    app = Application.builder().token(token).build()

    # Commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("menu", cmd_menu))
    app.add_handler(CommandHandler("balance", cmd_balance))

    # Admin ToyyibPay
    app.add_handler(CommandHandler("toyyib_show", toyyib_show))
    app.add_handler(CommandHandler("toyyib_enable", toyyib_enable))
    app.add_handler(CommandHandler("toyyib_sandbox", toyyib_sandbox))
    app.add_handler(CommandHandler("toyyib_setkey", toyyib_setkey))
    app.add_handler(CommandHandler("toyyib_setcat", toyyib_setcat))
    app.add_handler(CommandHandler("toyyib_setreturn", toyyib_setreturn))
    app.add_handler(CommandHandler("toyyib_setcallback", toyyib_setcallback))
    app.add_handler(CommandHandler("toyyib_restart", toyyib_restart))

    # Main menu/router + conversations
    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(menu_router, pattern=r"^(m:|t:)")],
        states={
            ST_SSH_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, ssh_user)],
            ST_SSH_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ssh_pass)],
            ST_SSH_DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ssh_days)],

            ST_VMESS_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, vmess_user)],
            ST_VMESS_BUG: [MessageHandler(filters.TEXT & ~filters.COMMAND, vmess_bug)],
            ST_VMESS_SNI: [MessageHandler(filters.TEXT & ~filters.COMMAND, vmess_sni)],
            ST_VMESS_DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, vmess_days)],

            ST_VLESS_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, vless_user)],
            ST_VLESS_BUG: [MessageHandler(filters.TEXT & ~filters.COMMAND, vless_bug)],
            ST_VLESS_SNI: [MessageHandler(filters.TEXT & ~filters.COMMAND, vless_sni)],
            ST_VLESS_DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, vless_days)],

            ST_TROJAN_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, trojan_user)],
            ST_TROJAN_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, trojan_pass)],
            ST_TROJAN_BUG: [MessageHandler(filters.TEXT & ~filters.COMMAND, trojan_bug)],
            ST_TROJAN_SNI: [MessageHandler(filters.TEXT & ~filters.COMMAND, trojan_sni)],
            ST_TROJAN_DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, trojan_days)],

            ST_RENEW_PROTO: [CallbackQueryHandler(renew_select_proto, pattern=r"^r:")],
            ST_RENEW_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, renew_user)],
            ST_RENEW_DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, renew_days)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )
    app.add_handler(conv)

    # extra menu buttons
    app.add_handler(CallbackQueryHandler(go_home, pattern=r"^m:home$"))
    app.add_handler(CallbackQueryHandler(show_accounts, pattern=r"^m:accounts$"))
    app.add_handler(CallbackQueryHandler(show_topup, pattern=r"^m:topup$"))

    return app


def main() -> None:
    cfg = load_config(DEFAULT_CONFIG_PATH)
    if not cfg.token:
        raise SystemExit("MPBOT token belum diset. Sila isi /etc/mpbot/config.json")

    app = build_app(cfg.token)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
