\
from __future__ import annotations

import os
import asyncio
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from .config import Settings, load_settings
from .db import Database, User, utcnow, str_to_dt
from .i18n import t, normalize_lang
from .keyboards import (
    kb_agreement,
    kb_back,
    kb_buy_star,
    kb_buy_vip,
    kb_invoice,
    kb_language,
    kb_main_menu,
    kb_protocols,
    kb_subscription,
    kb_verify_channels,
    kb_admin,
)
from .server_pool import AgentError, select_server, create_vpn_account
from .subscription import check_user_subscriptions
from .toyyibpay import ToyyibPayClient


def _fmt_date(dt: datetime | None) -> str:
    if not dt:
        return "-"
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d")


async def ensure_user(db: Database, msg: Message, settings: Settings) -> User:
    deep = (msg.text or "").strip()
    referred_by = None
    if deep.startswith("/start"):
        parts = deep.split(maxsplit=1)
        if len(parts) == 2 and parts[1].startswith("ref_"):
            try:
                referred_by = int(parts[1].replace("ref_", "").strip())
            except Exception:
                referred_by = None

    user = await db.upsert_user(
        user_id=msg.from_user.id,
        first_name=msg.from_user.first_name,
        username=msg.from_user.username,
        referred_by=referred_by,
    )

    # record referral relation (only for new user, but safe to call)
    if referred_by:
        await db.record_referral(referred_by, msg.from_user.id)

    return user


async def render_gate(bot: Bot, db: Database, settings: Settings, chat_id: int, user: User) -> None:
    lang = normalize_lang(user.language)

    if user.is_blocked:
        await bot.send_message(chat_id, t(lang, "blocked"))
        return

    if not user.is_subscribed:
        await bot.send_message(
            chat_id,
            t(lang, "subscribe_required"),
            reply_markup=kb_subscription(settings, lang),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if not user.agreement_accepted:
        await bot.send_message(
            chat_id,
            t(lang, "agreement_required"),
            reply_markup=kb_agreement(settings, lang),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    # show menu
    await bot.send_message(
        chat_id,
        f"{t(lang,'welcome_back')}\n💳 {t(lang,'menu_choose')}",
        reply_markup=kb_main_menu(lang),
    )


async def render_menu_message(bot: Bot, db: Database, settings: Settings, chat_id: int, user: User) -> None:
    lang = normalize_lang(user.language)
    await bot.send_message(
        chat_id,
        f"{t(lang,'welcome_back')}\n💳 {t(lang,'menu_choose')}",
        reply_markup=kb_main_menu(lang),
    )


async def invoice_watcher(bot: Bot, db: Database, settings: Settings) -> None:
    """
    Background loop:
    - mark expired invoices
    - increment unpaid strikes
    - auto block at 3 strikes
    """
    while True:
        try:
            expired = await db.list_expired_unprocessed_invoices()
            for inv in expired:
                await db.mark_invoice_expired(int(inv["id"]))
                strikes = await db.add_unpaid_strike(int(inv["user_id"]))
                if strikes >= 3:
                    await db.set_blocked(int(inv["user_id"]), True)
                    # notify user & admin
                    try:
                        user = await db.get_user(int(inv["user_id"]))
                        lang = normalize_lang(user.language if user else "ms")
                        await bot.send_message(int(inv["user_id"]), t(lang, "blocked_unpaid"))
                    except Exception:
                        pass
                    try:
                        await bot.send_message(settings.admin_id, f"⛔ Auto blocked user {inv['user_id']} (3 unpaid invoices).")
                    except Exception:
                        pass
        except Exception:
            pass
        await asyncio.sleep(60)


def build_rules_text(lang: str) -> str:
    return t(lang, "rules_short")


async def main() -> None:
    settings = load_settings()
    db = Database(settings.db_path)
    await db.init()

    bot = Bot(token=settings.main_bot_token, parse_mode=ParseMode.HTML)
    dp = Dispatcher()

    toyyib = None
    if settings.toyyibpay_enabled and settings.toyyibpay_user_secret_key and settings.toyyibpay_category_code:
        toyyib = ToyyibPayClient(
            user_secret_key=settings.toyyibpay_user_secret_key,
            category_code=settings.toyyibpay_category_code,
            is_sandbox=settings.toyyibpay_is_sandbox,
            timeout_sec=settings.agent_timeout_sec,
        )

    # Background watcher
    asyncio.create_task(invoice_watcher(bot, db, settings))

    @dp.message(CommandStart())
    async def on_start(message: Message) -> None:
        user = await ensure_user(db, message, settings)
        await bot.send_message(message.chat.id, t(normalize_lang(user.language), "welcome"))
        await render_gate(bot, db, settings, message.chat.id, user)

    @dp.message(Command("admin"))
    async def admin_cmd(message: Message) -> None:
        user = await db.get_user(message.from_user.id)
        if not user:
            return
        if message.from_user.id != settings.admin_id:
            return
        lang = normalize_lang(user.language)
        await message.answer("🛠 Admin Menu", reply_markup=kb_admin(lang))

    @dp.message(Command("addserver"))
    async def addserver_cmd(message: Message) -> None:
        """
        /addserver FREE name https://1.2.3.4:7000 API_KEY 100
        """
        if message.from_user.id != settings.admin_id:
            return
        parts = (message.text or "").split()
        if len(parts) < 6:
            await message.answer("Usage: /addserver FREE|STAR name base_url api_key max_users")
            return
        pool = parts[1].upper()
        name = parts[2]
        base_url = parts[3]
        api_key = parts[4]
        max_users = int(parts[5])
        sid = await db.add_server(pool, name, base_url, api_key, max_users=max_users)
        await message.answer(f"✅ Server added id={sid}")

    @dp.message(Command("servers"))
    async def servers_cmd(message: Message) -> None:
        if message.from_user.id != settings.admin_id:
            return
        servers = await db.list_servers()
        if not servers:
            await message.answer("No servers in DB. Use /addserver ...")
            return
        lines = []
        for s in servers:
            lines.append(f"#{s['id']} pool={s['pool']} enabled={s['enabled']} max={s['max_users']} name={s['name']} url={s['base_url']}")
        await message.answer("\n".join(lines))

    @dp.message(Command("enableserver"))
    async def enableserver_cmd(message: Message) -> None:
        if message.from_user.id != settings.admin_id:
            return
        parts = (message.text or "").split()
        if len(parts) < 2:
            await message.answer("Usage: /enableserver <id>")
            return
        await db.set_server_enabled(int(parts[1]), True)
        await message.answer("✅ enabled")

    @dp.message(Command("disableserver"))
    async def disableserver_cmd(message: Message) -> None:
        if message.from_user.id != settings.admin_id:
            return
        parts = (message.text or "").split()
        if len(parts) < 2:
            await message.answer("Usage: /disableserver <id>")
            return
        await db.set_server_enabled(int(parts[1]), False)
        await message.answer("✅ disabled")

    @dp.message(Command("unblock"))
    async def unblock_cmd(message: Message) -> None:
        if message.from_user.id != settings.admin_id:
            return
        parts = (message.text or "").split()
        if len(parts) < 2:
            await message.answer("Usage: /unblock <user_id>")
            return
        uid = int(parts[1])
        await db.set_blocked(uid, False)
        await db.reset_unpaid_strikes(uid)
        await message.answer(f"✅ unblocked {uid}")

    # -------- Callbacks --------

    @dp.callback_query(F.data == "act:menu")
    async def act_menu(cb: CallbackQuery) -> None:
        user = await db.get_user(cb.from_user.id)
        if not user:
            await cb.answer()
            return
        await cb.answer()
        await render_gate(bot, db, settings, cb.message.chat.id, user)

    @dp.callback_query(F.data == "act:check_sub")
    async def act_check_sub(cb: CallbackQuery) -> None:
        user = await db.get_user(cb.from_user.id)
        if not user:
            await cb.answer()
            return
        lang = normalize_lang(user.language)
        ok, missing = await check_user_subscriptions(bot, cb.from_user.id, settings.required_channels)
        if not ok:
            await cb.answer()
            await cb.message.answer(t(lang, "subscription_fail"))
            return
        # mark subscribed and give 1 credit if first time
        first_time, gave_credit = await db.mark_subscribed(cb.from_user.id, give_credit_if_first=True)
        # qualify referral & possibly award credit
        referrer_id = await db.qualify_referral_if_needed(cb.from_user.id)
        if referrer_id:
            # award every 3 referrals => 1 credit (cap 90)
            await db.maybe_award_referral_credit(referrer_id, max_refs=90)

        await cb.answer()
        if first_time and gave_credit:
            await cb.message.answer(t(lang, "subscription_ok"), parse_mode=ParseMode.MARKDOWN)
        else:
            await cb.message.answer(t(lang, "subscription_already_ok"))
        # proceed to agreement
        user = await db.get_user(cb.from_user.id)
        if user and not user.agreement_accepted:
            await cb.message.answer(
                t(lang, "agreement_required"),
                reply_markup=kb_agreement(settings, lang),
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            await render_gate(bot, db, settings, cb.message.chat.id, user)  # type: ignore

    @dp.callback_query(F.data == "act:accept_agreement")
    async def act_accept_agreement(cb: CallbackQuery) -> None:
        user = await db.get_user(cb.from_user.id)
        if not user:
            await cb.answer()
            return
        lang = normalize_lang(user.language)
        await db.accept_agreement(cb.from_user.id)
        await cb.answer()
        await cb.message.answer("✅ Accepted.")
        user = await db.get_user(cb.from_user.id)
        await render_gate(bot, db, settings, cb.message.chat.id, user)  # type: ignore

    @dp.callback_query(F.data == "act:verify")
    async def act_verify(cb: CallbackQuery) -> None:
        user = await db.get_user(cb.from_user.id)
        if not user:
            await cb.answer()
            return
        lang = normalize_lang(user.language)
        if not user.is_subscribed:
            await cb.answer()
            await cb.message.answer(t(lang, "subscribe_required"), reply_markup=kb_subscription(settings, lang), parse_mode=ParseMode.MARKDOWN)
            return
        if not user.agreement_accepted:
            await cb.answer()
            await cb.message.answer(t(lang, "agreement_required"), reply_markup=kb_agreement(settings, lang), parse_mode=ParseMode.MARKDOWN)
            return

        free_used = await db.count_claims_last_hour("free")
        star_until = str_to_dt(user.star_active_until)
        star_str = t(lang, "star_active", until=_fmt_date(star_until)) if (star_until and star_until > utcnow()) else t(lang, "star_inactive")
        await cb.answer()
        await cb.message.answer(
            t(
                lang,
                "select_channel",
                free_used=free_used,
                free_limit=settings.free_slots_per_hour,
                credits=user.credits,
                vip=user.vip_coins,
                star=star_str,
            ),
            reply_markup=kb_verify_channels(lang),
            parse_mode=ParseMode.MARKDOWN,
        )

    @dp.callback_query(F.data == "act:convert")
    async def act_convert(cb: CallbackQuery) -> None:
        user = await db.get_user(cb.from_user.id)
        if not user:
            await cb.answer()
            return
        lang = normalize_lang(user.language)
        if not user.is_subscribed:
            await cb.answer()
            await cb.message.answer(t(lang, "subscribe_required"), reply_markup=kb_subscription(settings, lang), parse_mode=ParseMode.MARKDOWN)
            return
        if not user.agreement_accepted:
            await cb.answer()
            await cb.message.answer(t(lang, "agreement_required"), reply_markup=kb_agreement(settings, lang), parse_mode=ParseMode.MARKDOWN)
            return

        await cb.answer()
        await cb.message.answer(
            t(lang, "convert_info", credits=user.credits),
            reply_markup=kb_protocols(lang, "convert", "convert"),
            parse_mode=ParseMode.MARKDOWN,
        )

    @dp.callback_query(F.data == "act:profile")
    async def act_profile(cb: CallbackQuery) -> None:
        user = await db.get_user(cb.from_user.id)
        if not user:
            await cb.answer()
            return
        lang = normalize_lang(user.language)
        claimed = await db.count_claimed_total(user.user_id)
        star_until = str_to_dt(user.star_active_until)
        star_str = t(lang, "star_active", until=_fmt_date(star_until)) if (star_until and star_until > utcnow()) else t(lang, "star_inactive")
        await cb.answer()
        await cb.message.answer(
            t(
                lang,
                "profile",
                user_id=user.user_id,
                credits=user.credits,
                vip=user.vip_coins,
                star=star_str,
                refs=user.referrals_count,
                claimed=claimed,
                spent=f"{user.total_spent:.2f}",
                joined=user.joined_at.split("T")[0],
                free_limit=settings.free_slots_per_hour,
            ),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb_back(lang),
        )

    @dp.callback_query(F.data == "act:invite")
    async def act_invite(cb: CallbackQuery) -> None:
        user = await db.get_user(cb.from_user.id)
        if not user:
            await cb.answer()
            return
        lang = normalize_lang(user.language)
        link = f"https://t.me/{settings.bot_username}?start=ref_{user.user_id}"
        await cb.answer()
        await cb.message.answer(
            t(lang, "invite", refs=user.referrals_count, credits=user.credits, link=link),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb_back(lang),
        )

    @dp.callback_query(F.data == "act:checkin")
    async def act_checkin(cb: CallbackQuery) -> None:
        user = await db.get_user(cb.from_user.id)
        if not user:
            await cb.answer()
            return
        lang = normalize_lang(user.language)
        if not await db.can_checkin_today(user.user_id):
            await cb.answer()
            await cb.message.answer(t(lang, "checkin_already"), reply_markup=kb_back(lang))
            return
        points = await db.do_checkin(user.user_id)
        await cb.answer()
        await cb.message.answer(t(lang, "checkin_ok", points=points), reply_markup=kb_back(lang))

    @dp.callback_query(F.data == "act:lang")
    async def act_lang(cb: CallbackQuery) -> None:
        user = await db.get_user(cb.from_user.id)
        if not user:
            await cb.answer()
            return
        lang = normalize_lang(user.language)
        await cb.answer()
        await cb.message.answer(t(lang, "lang_choose"), reply_markup=kb_language(lang))

    @dp.callback_query(F.data.startswith("setlang:"))
    async def setlang(cb: CallbackQuery) -> None:
        lang = cb.data.split(":", 1)[1]
        if lang not in ("ms", "en", "zh"):
            await cb.answer()
            return
        await db.set_language(cb.from_user.id, lang)
        await cb.answer()
        user = await db.get_user(cb.from_user.id)
        await render_gate(bot, db, settings, cb.message.chat.id, user)  # type: ignore

    @dp.callback_query(F.data == "act:support")
    async def act_support(cb: CallbackQuery) -> None:
        user = await db.get_user(cb.from_user.id)
        if not user:
            await cb.answer()
            return
        lang = normalize_lang(user.language)
        support_bot = settings.support_bot_token and "@"+ (settings.support_bot_token[:0] or "fvpngensupportbot")
        # can't derive username from token; use config bot_username? We'll use hardcoded env SUPPORT_BOT_USERNAME optional.
        support_username = (os.getenv("SUPPORT_BOT_USERNAME") or "fvpngensupportbot").lstrip("@")
        await cb.answer()
        await cb.message.answer(t(lang, "support_hint", support_bot=support_username), reply_markup=kb_back(lang))

    # --- Payment ---

    @dp.callback_query(F.data == "act:buy_vip")
    async def act_buy_vip(cb: CallbackQuery) -> None:
        user = await db.get_user(cb.from_user.id)
        if not user:
            await cb.answer()
            return
        lang = normalize_lang(user.language)
        if not settings.toyyibpay_enabled or not toyyib:
            await cb.answer()
            await cb.message.answer("ToyyibPay is not configured.")
            return
        await cb.answer()
        await cb.message.answer(t(lang, "payment_warning"), parse_mode=ParseMode.MARKDOWN)
        await cb.message.answer(t(lang, "buy_vip_title", vip=user.vip_coins), reply_markup=kb_buy_vip(lang), parse_mode=ParseMode.MARKDOWN)

    @dp.callback_query(F.data.startswith("buyvip:"))
    async def buyvip(cb: CallbackQuery) -> None:
        user = await db.get_user(cb.from_user.id)
        if not user:
            await cb.answer()
            return
        if user.is_blocked:
            await cb.answer()
            return
        lang = normalize_lang(user.language)
        if not settings.toyyibpay_enabled or not toyyib:
            await cb.answer()
            await cb.message.answer("ToyyibPay is not configured.")
            return

        _, qty_s, myr_s = cb.data.split(":")
        qty = int(qty_s)
        amount_myr = float(myr_s)

        external_ref = f"vipcoin-{cb.from_user.id}-{secrets.token_hex(4)}"
        bill_code, bill_url = await toyyib.create_bill(
            bill_name="VIP Coins",
            bill_description=f"VIP Coins x{qty}",
            amount_myr=amount_myr,
            external_ref=external_ref,
            return_url=settings.toyyibpay_return_url,
            callback_url=settings.toyyibpay_callback_url or None,
        )
        invoice_id = await db.create_invoice(cb.from_user.id, "vip_coin", amount_myr, qty, bill_code, bill_url, settings.invoice_expire_minutes, meta={"external_ref": external_ref})
        await cb.answer()
        await cb.message.answer(
            t(lang, "invoice_created", type="VIP Coins", amount=amount_myr, mins=settings.invoice_expire_minutes),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb_invoice(lang, invoice_id, bill_url),
        )

    @dp.callback_query(F.data == "act:buy_star")
    async def act_buy_star(cb: CallbackQuery) -> None:
        user = await db.get_user(cb.from_user.id)
        if not user:
            await cb.answer()
            return
        lang = normalize_lang(user.language)
        if not settings.toyyibpay_enabled or not toyyib:
            await cb.answer()
            await cb.message.answer("ToyyibPay is not configured.")
            return
        await cb.answer()
        await cb.message.answer(t(lang, "payment_warning"), parse_mode=ParseMode.MARKDOWN)
        await cb.message.answer(t(lang, "buy_star_title"), reply_markup=kb_buy_star(lang), parse_mode=ParseMode.MARKDOWN)

    @dp.callback_query(F.data.startswith("buystar:"))
    async def buystar(cb: CallbackQuery) -> None:
        user = await db.get_user(cb.from_user.id)
        if not user:
            await cb.answer()
            return
        if user.is_blocked:
            await cb.answer()
            return
        lang = normalize_lang(user.language)
        if not settings.toyyibpay_enabled or not toyyib:
            await cb.answer()
            await cb.message.answer("ToyyibPay is not configured.")
            return

        amount_myr = 250.0
        external_ref = f"star-{cb.from_user.id}-{secrets.token_hex(4)}"
        bill_code, bill_url = await toyyib.create_bill(
            bill_name="VIP Star",
            bill_description="VIP Star 30 days",
            amount_myr=amount_myr,
            external_ref=external_ref,
            return_url=settings.toyyibpay_return_url,
            callback_url=settings.toyyibpay_callback_url or None,
        )
        invoice_id = await db.create_invoice(cb.from_user.id, "star", amount_myr, 1, bill_code, bill_url, settings.invoice_expire_minutes, meta={"external_ref": external_ref})
        await cb.answer()
        await cb.message.answer(
            t(lang, "invoice_created", type="VIP Star", amount=amount_myr, mins=settings.invoice_expire_minutes),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb_invoice(lang, invoice_id, bill_url),
        )

    @dp.callback_query(F.data.startswith("invcheck:"))
    async def invcheck(cb: CallbackQuery) -> None:
        user = await db.get_user(cb.from_user.id)
        if not user:
            await cb.answer()
            return
        lang = normalize_lang(user.language)
        if not settings.toyyibpay_enabled or not toyyib:
            await cb.answer()
            await cb.message.answer("ToyyibPay is not configured.")
            return
        invoice_id = int(cb.data.split(":")[1])
        inv = await db.get_invoice(invoice_id)
        if not inv or int(inv["user_id"]) != cb.from_user.id:
            await cb.answer()
            return
        if inv["status"] == "paid":
            await cb.answer()
            await cb.message.answer(t(lang, "invoice_paid"))
            return
        if inv["status"] == "expired":
            await cb.answer()
            await cb.message.answer(t(lang, "invoice_expired"))
            return

        # check paid
        paid = await toyyib.is_bill_paid(inv["bill_code"])
        if not paid:
            await cb.answer()
            await cb.message.answer(t(lang, "invoice_pending"))
            return

        # mark paid
        await db.mark_invoice_paid(invoice_id)
        await db.reset_unpaid_strikes(cb.from_user.id)
        inv_type = inv["type"]
        amount = float(inv["amount_myr"])
        if inv_type == "vip_coin":
            qty = int(inv["qty"])
            await db.add_vip_coins(cb.from_user.id, qty)
            await db.increment_total_spent(cb.from_user.id, amount)
        elif inv_type == "star":
            until = utcnow() + timedelta(days=settings.star_subscription_days)
            await db.set_star_until(cb.from_user.id, until)
            await db.increment_total_spent(cb.from_user.id, amount)

        await cb.answer()
        await cb.message.answer(t(lang, "invoice_paid"))
        # back to menu
        user = await db.get_user(cb.from_user.id)
        await render_gate(bot, db, settings, cb.message.chat.id, user)  # type: ignore

    # --- Verify channel selection ---
    @dp.callback_query(F.data.startswith("verify:"))
    async def verify_channel(cb: CallbackQuery) -> None:
        user = await db.get_user(cb.from_user.id)
        if not user:
            await cb.answer()
            return
        lang = normalize_lang(user.language)
        if user.is_blocked:
            await cb.answer()
            await cb.message.answer(t(lang, "blocked"))
            return
        channel = cb.data.split(":")[1]
        if channel not in ("free", "vip", "star"):
            await cb.answer()
            return

        if channel == "free":
            free_used = await db.count_claims_last_hour("free")
            if free_used >= settings.free_slots_per_hour:
                await cb.answer()
                await cb.message.answer(t(lang, "free_full", free_used=free_used, free_limit=settings.free_slots_per_hour))
                return
            if user.credits < settings.free_claim_cost_credits:
                await cb.answer()
                await cb.message.answer(t(lang, "need_credits"))
                return
        elif channel == "vip":
            if user.vip_coins < settings.vip_claim_cost_vip_coins:
                await cb.answer()
                await cb.message.answer(t(lang, "need_vip_coins"))
                return
        elif channel == "star":
            star_until = str_to_dt(user.star_active_until)
            if not (star_until and star_until > utcnow()):
                await cb.answer()
                await cb.message.answer(t(lang, "star_inactive"))
                return

        await cb.answer()
        await cb.message.answer(t(lang, "select_protocol"), reply_markup=kb_protocols(lang, "claim", channel))

    # --- Claim / Convert ---
    @dp.callback_query(F.data.startswith("claim:") | F.data.startswith("convert:"))
    async def do_claim(cb: CallbackQuery) -> None:
        user = await db.get_user(cb.from_user.id)
        if not user:
            await cb.answer()
            return
        lang = normalize_lang(user.language)
        if user.is_blocked:
            await cb.answer()
            await cb.message.answer(t(lang, "blocked"))
            return

        parts = cb.data.split(":")
        action = parts[0]  # claim|convert
        channel = parts[1]
        protocol = parts[2]

        if protocol not in ("ssh", "vless", "trojan"):
            await cb.answer()
            return

        # prerequisites
        if not user.is_subscribed:
            await cb.answer()
            await cb.message.answer(t(lang, "subscribe_required"), reply_markup=kb_subscription(settings, lang), parse_mode=ParseMode.MARKDOWN)
            return
        if not user.agreement_accepted:
            await cb.answer()
            await cb.message.answer(t(lang, "agreement_required"), reply_markup=kb_agreement(settings, lang), parse_mode=ParseMode.MARKDOWN)
            return

        # determine cost & validity & pool
        cost_credits = 0
        cost_vip = 0
        days = 3
        pool = "FREE"

        if action == "convert":
            days = settings.convert_validity_days
            cost_credits = settings.convert_cost_credits
            pool = "FREE"
            if user.credits < cost_credits:
                await cb.answer()
                await cb.message.answer(t(lang, "convert_need", need=cost_credits))
                return
        else:
            if channel == "free":
                days = settings.free_claim_validity_days
                cost_credits = settings.free_claim_cost_credits
                pool = "FREE"
                free_used = await db.count_claims_last_hour("free")
                if free_used >= settings.free_slots_per_hour:
                    await cb.answer()
                    await cb.message.answer(t(lang, "free_full", free_used=free_used, free_limit=settings.free_slots_per_hour))
                    return
                if user.credits < cost_credits:
                    await cb.answer()
                    await cb.message.answer(t(lang, "need_credits"))
                    return
            elif channel == "vip":
                days = settings.vip_claim_validity_days
                cost_vip = settings.vip_claim_cost_vip_coins
                pool = "FREE"
                if user.vip_coins < cost_vip:
                    await cb.answer()
                    await cb.message.answer(t(lang, "need_vip_coins"))
                    return
            elif channel == "star":
                days = settings.vip_claim_validity_days  # still 3 days
                pool = "STAR"
                star_until = str_to_dt(user.star_active_until)
                if not (star_until and star_until > utcnow()):
                    await cb.answer()
                    await cb.message.answer(t(lang, "star_inactive"))
                    return
            else:
                await cb.answer()
                return

        await cb.answer()
        await cb.message.answer(t(lang, "creating"))

        # select server + create
        server = await select_server(db, pool, bot, settings.admin_id, timeout_sec=settings.server_ping_timeout_sec)
        if not server:
            await cb.message.answer("🚫 Server not available right now.")
            return

        try:
            res = await create_vpn_account(server, protocol, days, timeout_sec=settings.agent_timeout_sec)
        except AgentError as e:
            await cb.message.answer(f"❌ {e.message}")
            return

        # Deduct balances (after success)
        if cost_credits:
            await db.add_credits(user.user_id, -cost_credits)
        if cost_vip:
            await db.add_vip_coins(user.user_id, -cost_vip)

        # Record claim
        await db.record_claim(
            user_id=user.user_id,
            protocol=protocol,
            days=days,
            channel=("convert" if action == "convert" else channel),
            server_id=int(server["id"]),
            cost_credits=cost_credits,
            cost_vip=cost_vip,
            result=res,
        )

        # Respond with account details
        rules = build_rules_text(lang)
        exp = res.get("expires_at", "-")
        if protocol == "ssh":
            details = res.get("details", {})
            await cb.message.answer(
                t(
                    lang,
                    "created_ssh",
                    username=details.get("username", "-"),
                    password=details.get("password", "-"),
                    host=details.get("host", details.get("domain", "-")),
                    days=days,
                    exp=exp,
                    rules=rules,
                ),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=kb_back(lang),
            )
        else:
            uri = res.get("details", {}).get("uri", "")
            # requirement: output link URI sahaja (vless://… / trojan://…)
            if uri:
                await cb.message.answer(uri)
            await cb.message.answer(
                t(lang, "created_info", days=days, exp=exp, rules=rules),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=kb_back(lang),
            )

    # Start polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    import os
    asyncio.run(main())
