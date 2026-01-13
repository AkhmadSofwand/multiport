\
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import httpx


@dataclass
class ToyyibPayClient:
    user_secret_key: str
    category_code: str
    is_sandbox: bool = False
    timeout_sec: int = 15

    @property
    def base_url(self) -> str:
        return "https://dev.toyyibpay.com" if self.is_sandbox else "https://toyyibpay.com"

    def _api(self, path: str) -> str:
        return f"{self.base_url}{path}"

    async def create_bill(
        self,
        *,
        bill_name: str,
        bill_description: str,
        amount_myr: float,
        external_ref: str,
        return_url: str,
        callback_url: str | None = None,
        payer_name: str = "",
        payer_email: str = "",
        payer_phone: str = "",
        payment_channel: str = "2",  # 0 FPX, 1 Card, 2 both
    ) -> Tuple[str, str]:
        """
        Returns (bill_code, bill_url)

        ToyyibPay expects amount in CENT (RM1 = 100).
        API ref: https://toyyibpay.com/apireference/ (Create Bill, Get Bill Transactions).
        """
        amount_cent = int(round(float(amount_myr) * 100))

        payload: Dict[str, Any] = {
            "userSecretKey": self.user_secret_key,
            "categoryCode": self.category_code,
            "billName": bill_name[:30],
            "billDescription": bill_description[:100],
            "billPriceSetting": 1,
            "billPayorInfo": 0,  # we don't force user to fill details
            "billAmount": amount_cent,
            "billReturnUrl": return_url,
            "billCallbackUrl": callback_url or "",
            "billExternalReferenceNo": external_ref,
            "billTo": payer_name,
            "billEmail": payer_email,
            "billPhone": payer_phone,
            "billSplitPayment": 0,
            "billSplitPaymentArgs": "",
            "billPaymentChannel": payment_channel,
            # keep ToyyibPay expiry simple; we handle "minute expiry" internally
            "billExpiryDays": 1,
        }

        async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
            r = await client.post(self._api("/index.php/api/createBill"), data=payload)
            r.raise_for_status()
            # response is JSON array string: [{"BillCode":"xxxx"}]
            data = r.json()
            if not isinstance(data, list) or not data or "BillCode" not in data[0]:
                raise RuntimeError(f"Unexpected ToyyibPay response: {r.text[:200]}")
            bill_code = data[0]["BillCode"]
            bill_url = f"{self.base_url}/{bill_code}"
            return bill_code, bill_url

    async def get_bill_transactions(self, bill_code: str) -> List[Dict[str, Any]]:
        payload = {"billCode": bill_code}
        async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
            r = await client.post(self._api("/index.php/api/getBillTransactions"), data=payload)
            r.raise_for_status()
            data = r.json()
            if isinstance(data, list):
                return data
            return []

    async def is_bill_paid(self, bill_code: str) -> bool:
        txs = await self.get_bill_transactions(bill_code)
        for tx in txs:
            # billpaymentStatus: "1" = successful transaction
            if str(tx.get("billpaymentStatus", "")).strip() == "1":
                return True
        return False
