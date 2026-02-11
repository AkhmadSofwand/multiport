import json
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

from mpbot.config import DEFAULT_CONFIG_PATH, load_config
from mpbot.db import DB

app = FastAPI()


def _truthy(v: str) -> bool:
    return str(v).strip() in {"1", "true", "True", "yes", "YES"}


@app.post("/toyyibpay/callback")
async def toyyibpay_callback(request: Request):
    cfg = load_config(DEFAULT_CONFIG_PATH)
    db = DB(cfg.db_path)

    # ToyyibPay biasanya hantar form-urlencoded
    form = await request.form()
    payload = {k: str(v) for k, v in form.items()}

    bill_code = payload.get("billcode") or payload.get("BillCode") or payload.get("billCode")
    status_id = payload.get("status_id") or payload.get("status") or payload.get("statusId")
    ref_no = payload.get("refno") or payload.get("refNo") or payload.get("transaction_id")

    if not bill_code:
        return PlainTextResponse("missing billcode", status_code=400)

    # status_id=1 biasanya berjaya
    paid = str(status_id).strip() == "1" or _truthy(str(status_id))

    # Update DB: credit ikut rekod topup, bukan ikut amount dari callback
    if paid:
        ok = db.mark_topup_paid(bill_code=bill_code, ref_no=ref_no or "", raw_payload=json.dumps(payload, ensure_ascii=False))
        if ok:
            return PlainTextResponse("ok")
        return PlainTextResponse("unknown bill", status_code=404)

    db.mark_topup_failed(bill_code=bill_code, raw_payload=json.dumps(payload, ensure_ascii=False))
    return PlainTextResponse("not paid")


@app.get("/healthz")
def healthz():
    return {"ok": True}
