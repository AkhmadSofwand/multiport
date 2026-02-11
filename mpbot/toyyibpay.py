from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx


@dataclass
class CreateBillResult:
    bill_code: str
    payment_url: str


class ToyyibPayError(RuntimeError):
    pass


def base_url(sandbox: bool) -> str:
    return "https://dev.toyyibpay.com" if sandbox else "https://toyyibpay.com"


async def create_bill(
    *,
    sandbox: bool,
    secret_key: str,
    category_code: str,
    bill_name: str,
    bill_desc: str,
    amount_cents: int,
    payer_name: str,
    payer_email: str,
    payer_phone: str,
    return_url: str,
    callback_url: str,
    reference_1: str,
) -> CreateBillResult:
    if amount_cents <= 0:
        raise ToyyibPayError("Jumlah tidak sah")
    if not secret_key or not category_code:
        raise ToyyibPayError("ToyyibPay belum dikonfigurasi (secret key/category code)")

    # ToyyibPay expects amount in cents (e.g. RM10 => 1000)
    payload = {
        "userSecretKey": secret_key,
        "categoryCode": category_code,
        "billName": bill_name,
        "billDescription": bill_desc,
        "billPriceSetting": 1,
        "billPayorInfo": 1,
        "billAmount": amount_cents,
        "billReturnUrl": return_url,
        "billCallbackUrl": callback_url,
        "billExternalReferenceNo": reference_1,
        "billTo": payer_name,
        "billEmail": payer_email,
        "billPhone": payer_phone,
    }

    url = f"{base_url(sandbox)}/index.php/api/createBill"
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(url, data=payload)

    if r.status_code != 200:
        raise ToyyibPayError(f"ToyyibPay createBill gagal HTTP {r.status_code}")

    try:
        data = r.json()
    except Exception as e:
        raise ToyyibPayError(f"ToyyibPay respons bukan JSON: {e}")

    # createBill returns list of dicts, first item contains BillCode
    if not isinstance(data, list) or not data or "BillCode" not in data[0]:
        raise ToyyibPayError(f"ToyyibPay createBill respons tak dijangka: {json.dumps(data)[:300]}")

    bill_code = str(data[0]["BillCode"]).strip()
    pay_url = f"{base_url(sandbox)}/{bill_code}"
    return CreateBillResult(bill_code=bill_code, payment_url=pay_url)


async def get_bill_transactions(
    *,
    sandbox: bool,
    secret_key: str,
    bill_code: str,
) -> Any:
    url = f"{base_url(sandbox)}/index.php/api/getBillTransactions"
    payload = {"userSecretKey": secret_key, "billCode": bill_code}
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(url, data=payload)
    if r.status_code != 200:
        raise ToyyibPayError(f"ToyyibPay getBillTransactions gagal HTTP {r.status_code}")
    return r.json()
