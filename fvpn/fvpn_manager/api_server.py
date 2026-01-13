from __future__ import annotations

import asyncio
from datetime import timedelta

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

from .config import load_settings
from .db import Database, utcnow
from .toyyibpay import ToyyibPayClient

app = FastAPI(title="FVPN Manager Callback API")


@app.get("/health")
async def health():
    return {"ok": True}


@app.post("/toyyibpay/callback")
async def toyyibpay_callback(request: Request):
    """
    ToyyibPay Callback (POST form).
    Common fields (may vary): refno, status, reason, billcode, order_id, amount, transaction_time.
    We treat status == '1' as success.
    """
    settings = load_settings()
    form = await request.form()
    billcode = str(form.get("billcode") or form.get("billCode") or "")
    status = str(form.get("status") or "")
    if not billcode:
        return PlainTextResponse("missing billcode", status_code=400)

    db = Database(settings.db_path)
    await db.init()

    inv = await db.find_pending_invoice_by_billcode(billcode)
    if not inv:
        return PlainTextResponse("invoice not found", status_code=404)

    if inv["status"] == "paid":
        return PlainTextResponse("ok")

    if status != "1":
        # not success; keep pending. The watcher will expire it later.
        return PlainTextResponse("pending")

    # mark paid and apply effects (double-check with getBillTransactions)
    toyyib = ToyyibPayClient(
        user_secret_key=settings.toyyibpay_user_secret_key,
        category_code=settings.toyyibpay_category_code,
        is_sandbox=settings.toyyibpay_is_sandbox,
        timeout_sec=settings.agent_timeout_sec,
    )
    if not await toyyib.is_bill_paid(billcode):
        return PlainTextResponse("pending")

    invoice_id = int(inv["id"])
    user_id = int(inv["user_id"])
    inv_type = inv["type"]
    amount = float(inv["amount_myr"])
    qty = int(inv["qty"])

    await db.mark_invoice_paid(invoice_id)
    await db.reset_unpaid_strikes(user_id)
    await db.increment_total_spent(user_id, amount)

    if inv_type == "vip_coin":
        await db.add_vip_coins(user_id, qty)
    elif inv_type == "star":
        until = utcnow() + timedelta(days=settings.star_subscription_days)
        await db.set_star_until(user_id, until)

    return PlainTextResponse("ok")
