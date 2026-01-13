# FVPN AutoScript (Manager + Worker Agent)

This project implements a **Telegram VPN Generator Bot** with:

- ✅ Free claim using **Credits** (1 credit → 3 days)
- ♻️ Convert **10 credits → 30 days** (ALL protocols)
- ⚡ VIP claim using **VIP Coins** (1 VIP coin → 3 days)
- ⭐ VIP Star subscription (**MYR250 / 30 days**) → unlimited claims (each ID still 3 days)
- 🎯 Referral system: **every 3 referrals = 1 credit**, max **90 referrals**
- ✅ Daily check-in: **+1 point/day**, every **30 points = 1 credit**
- 🧾 ToyyibPay payment invoice + unpaid tracking (**3 unpaid invoices = auto block**)
- 🖥️ Worker Agent API for multi-server pools:
  - Pool FREE = Free/VIP Coin claims
  - Pool STAR = VIP Star claims
  - Each server has **max 100 users** (configurable) and bot will rotate to next server automatically.

> ⚠️ Use only on servers you own/control and follow your hosting provider terms & local laws.

---

## 1) Install

### A) Manager Server (Bots + Callback API)

```bash
unzip fvpn_autoscript.zip
cd fvpn_autoscript
bash install.sh
# choose mode 1
```

After install:
- Main bot service: `fvpn-mainbot`
- Support bot service: `fvpn-supportbot` (optional)
- Callback API: `fvpn-callback-api` (optional)

### B) Worker Server (Agent API)

```bash
unzip fvpn_autoscript.zip
cd fvpn_autoscript
bash install.sh
# choose mode 2
```

After install:
- Agent service: `fvpn-agent`
- Default port: `7000`

---

## 2) Register Worker Servers inside the Bot (Admin)

From your Telegram **main bot**, send:

```text
/addserver FREE free1 https://WORKER_IP:7000 AGENT_API_KEY 100
/addserver STAR star1 https://WORKER_IP:7000 AGENT_API_KEY 100
```

Then check:

```text
/servers
```

---

## 3) Xray Config Compatibility (Important)

Worker Agent expects **multiport-style** config files with markers:

- VLESS TLS: `/usr/local/etc/xray/vless.json` containing `#tls`
- VLESS none: `/usr/local/etc/xray/vnone.json` containing `#none` (optional)
- TROJAN WS TLS: `/usr/local/etc/xray/trojanws.json` containing `#tls`
- Domain file: `/usr/local/etc/xray/domain`

If your server uses different paths, edit `/etc/fvpn/fvpn-agent.env`.

> If you use your own Xray config format, tell me and I can adjust the agent insertion logic.

---

## 4) Panel On/Off

Run:

```bash
fvpn-panel
```

You can start/stop/restart manager services or the worker agent.

---

## 5) Claim Rules (based on your UI)

- Free claim: **3 days**, cost **1 credit**
- Convert: **10 credits → 30 days**, applies to **all protocols**
- VIP claim: **3 days**, cost **1 VIP coin**
- VIP Star: Subscription **30 days**, each created ID still **3 days**
- Free rate-limit: **20 slots/hour**
- Server limit: **100 users/server** (when full, bot notifies admin)

---

## 6) Output Format

For protocol **VLESS** and **Trojan**, bot sends **URI link only**:

- `vless://...`
- `trojan://...`

For **SSH**, bot sends generated `username/password`.

---

## 7) Notes

- ToyyibPay callback is optional. Polling via "Check Payment" works without callback.
- If you expose callback API publicly, set `TOYYIBPAY_CALLBACK_URL` to:
  `https://YOUR_DOMAIN/toyyibpay/callback`

---

Need custom UI texts, extra features, or changes? Tell me what you want next.
