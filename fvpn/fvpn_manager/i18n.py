from __future__ import annotations

from typing import Any, Dict


_LANGS = ("ms", "en", "zh")


# NOTE: Keep texts short. Telegram has message limits.
MESSAGES: Dict[str, Dict[str, str]] = {
    "en": {
        "welcome": "👋 Welcome to Free VPN Generator!",
        "welcome_back": "👋 Welcome back!",
        "subscribe_required": (
            "⚠️ To use this bot, you need to subscribe to our channels first:\n\n"
            "1️⃣ Subscribe to all channels below\n"
            "2️⃣ Press '✅ Check Subscription'\n"
            "3️⃣ Get access to the bot!\n\n"
            "💳 After subscription you will receive **1 free credit** to your account!"
        ),
        "subscription_ok": "✅ Thank you for subscribing!\n\n💳 You received **1 free credit** to your account!\n\nNow you can use the bot.",
        "subscription_already_ok": "✅ Subscription verified. You can use the bot.",
        "subscription_fail": "❌ You are not subscribed to all required channels!\n\nPlease subscribe to ALL channels and try again.",
        "agreement_required": (
            "📜 **User Agreement Required**\n\n"
            "Before using the bot, please read and accept our User Agreement:\n"
            "👉 Read User Agreement\n\n"
            "By clicking “I Accept”, you confirm that you have read and agree to all terms and conditions.\n\n"
            "⚠️ You cannot use the bot without accepting the agreement."
        ),
        "blocked": "⛔ Your account is blocked. Please contact support.",
        "menu_choose": "Choose an action below:",
        "btn_check_sub": "✅ Check Subscription",
        "btn_accept": "✅ I Accept",
        "btn_read_agreement": "👉 Read User Agreement",
        "btn_verify": "✅ Verify",
        "btn_convert": "♻️ Convert 10 Credits → 30 Days",
        "btn_buy_vip": "💰 Buy VIP Coins",
        "btn_buy_star": "⭐ VIP Star (30 days)",
        "btn_invite": "👥 Invite Friends",
        "btn_profile": "👤 My Profile",
        "btn_checkin": "✅ Daily Check-in",
        "btn_language": "🌐 Language",
        "btn_support": "🆘 Support",
        "btn_back": "◀️ Back",
        "select_channel": (
            "🔄 **Select Verification Channel**\n\n"
            "🆓 Normal Channel - Free ({free_used}/{free_limit} slots/hour)\n"
            "⚡ VIP Channel - Instant (uses VIP Coins)\n"
            "⭐ Star Premium - Unlimited (MYR250/month)\n\n"
            "Your balance:\n"
            "🔵 Credits: {credits}\n"
            "⚡ VIP Coins: {vip}\n"
            "⭐ Star: {star}\n"
        ),
        "star_active": "✅ Active until {until}",
        "star_inactive": "❌ Not active",
        "need_credits": "❌ Sorry! Your credits balance is not enough.",
        "need_vip_coins": "❌ Sorry! Your VIP Coins balance is not enough.",
        "free_full": "⚠️ Free channel is full right now ({free_used}/{free_limit} slots/hour). Please try later or use VIP Coins.",
        "select_protocol": "🔧 Choose protocol:",
        "proto_ssh": "SSH",
        "proto_vless": "VLESS",
        "proto_trojan": "Trojan",
        "creating": "⏳ Creating your ID…",
        "created_ssh": (
            "✅ **SSH ID Created**\n\n"
            "Username: `{username}`\n"
            "Password: `{password}`\n"
            "Host: `{host}`\n"
            "Port: `22`\n"
            "Valid: **{days} days**\n"
            "Expired: `{exp}`\n\n"
            "📌 Rules:\n{rules}"
        ),
        "created_uri": (
            "✅ **{proto} ID Created**\n\n"
            "{uri}\n\n"
            "Valid: **{days} days**\n"
            "Expired: `{exp}`\n\n"
            "📌 Rules:\n{rules}"
        ),
        "rules_short": (
            "• No DDoS / flooding\n"
            "• No torrent / P2P\n"
            "• No abuse / hacking / spam\n"
            "• No multi-login / sharing account\n"
            "• Violation = ban (no refund)"
        ),
        "profile": (
            "👤 **Your Profile**\n\n"
            "🆔 ID: `{user_id}`\n"
            "🔵 Credits: `{credits}` (free, limit {free_limit}/hour)\n"
            "⚡ VIP Coins: `{vip}` (1 coin per claim)\n"
            "⭐ Star: {star}\n"
            "👥 Referrals: `{refs}`\n"
            "✅ Claimed: `{claimed}`\n"
            "💵 Total Spent: `MYR{spent}`\n"
            "📅 Joined: `{joined}`\n"
        ),
        "invite": (
            "👥 **Invite Friends Program**\n\n"
            "Share your referral link and get FREE credit!\n\n"
            "📋 How it works:\n"
            "1. Share your link with friends\n"
            "2. They subscribe to the channel\n"
            "3. Every 3 friends = 1 credit!\n\n"
            "⚠️ Important: Maximum 90 referrals count. After reaching 90, no more credits will be awarded.\n\n"
            "👥 Your referrals: {refs}\n"
            "💳 Your credits: {credits}\n\n"
            "🔗 Your referral link:\n{link}\n\n"
            "💡 We appreciate your understanding! Server costs are high."
        ),
        "checkin_ok": "✅ Check-in successful!\n💰 Earned: +1 point\n💳 Current points: {points}\n\n(Note: 30 points = 1 credit)",
        "checkin_already": "ℹ️ You already checked in today. Come back tomorrow!",
        "payment_warning": (
            "⚠️ **IMPORTANT WARNING:**\n\n"
            "Creating a payment invoice and NOT paying is tracked!\n"
            "If you open invoices without paying 3+ times, your account will be AUTOMATICALLY BLOCKED.\n\n"
            "Only proceed if you intend to complete the payment.\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        ),
        "buy_vip_title": (
            "💰 **Buy VIP Coins**\n"
            "💳 Your balance: {vip} VIP coins\n\n"
            "📦 Select a package:"
        ),
        "buy_star_title": (
            "⭐ **VIP Star Subscription**\n\n"
            "💎 Price: MYR250\n"
            "⏱ Duration: 30 days\n\n"
            "Benefits:\n"
            "✅ UNLIMITED ID for 30 days\n"
            "✅ No credit deduction per ID\n"
            "✅ VIP badge in profile\n\n"
            "Click the button below to purchase:"
        ),
        "invoice_created": (
            "🧾 **Invoice Created**\n\n"
            "Type: {type}\n"
            "Amount: MYR{amount}\n\n"
            "➡️ Click **Pay Now** to open ToyyibPay payment page.\n"
            "After payment, click **Check Payment**.\n\n"
            "Invoice expires in {mins} minutes."
        ),
        "invoice_paid": "✅ Payment received! Your balance has been updated.",
        "invoice_pending": "⏳ Payment not detected yet. If you already paid, wait 1-2 minutes and try again.",
        "invoice_expired": "❌ Invoice expired / not paid.",
        "blocked_unpaid": "⛔ You opened invoices without paying 3 times. Your account is now blocked. Contact support.",
        "lang_choose": "🌐 Choose language:",
        "lang_ms": "Bahasa Melayu",
        "lang_en": "English",
        "lang_zh": "中文",
        "support_hint": "🆘 For support, please open: @{support_bot}",
        "convert_info": (
            "♻️ **Convert Credits**\n\n"
            "💡 Example: 10 credits = ID 30 days\n"
            "This conversion applies to **ALL protocols**.\n\n"
            "Your credits: {credits}"
        ),
        "convert_need": "❌ Sorry! Your credits balance is not enough. Need {need} credits.",
        "created_info": (
            "Valid: **{days} days**\n"
            "Expired: `{exp}`\n\n"
            "📌 Rules:\n{rules}"
        ),

    },
    "ms": {
        "welcome": "👋 Selamat datang ke Free VPN Generator!",
        "welcome_back": "👋 Selamat kembali!",
        "subscribe_required": (
            "⚠️ Untuk guna bot ini, anda perlu subscribe channel dahulu:\n\n"
            "1️⃣ Subscribe semua channel di bawah\n"
            "2️⃣ Tekan '✅ Semak Subscription'\n"
            "3️⃣ Dapatkan akses bot!\n\n"
            "💳 Selepas subscribe anda akan dapat **1 kredit percuma**!"
        ),
        "subscription_ok": "✅ Terima kasih kerana subscribe!\n\n💳 Anda menerima **1 kredit percuma**!\n\nSekarang anda boleh guna bot.",
        "subscription_already_ok": "✅ Subscription disahkan. Anda boleh guna bot.",
        "subscription_fail": "❌ Anda belum subscribe semua channel yang diperlukan!\n\nSila subscribe SEMUA channel dan cuba lagi.",
        "agreement_required": (
            "📜 **User Agreement Diperlukan**\n\n"
            "Sebelum guna bot, sila baca & terima User Agreement:\n"
            "👉 Read User Agreement\n\n"
            "Dengan klik “I Accept”, anda mengesahkan anda telah baca & bersetuju.\n\n"
            "⚠️ Anda tidak boleh guna bot tanpa terima agreement."
        ),
        "blocked": "⛔ Akaun anda telah diblock. Sila hubungi support.",
        "menu_choose": "Pilih tindakan di bawah:",
        "btn_check_sub": "✅ Semak Subscription",
        "btn_accept": "✅ I Accept",
        "btn_read_agreement": "👉 Read User Agreement",
        "btn_verify": "✅ Verify",
        "btn_convert": "♻️ Convert 10 Credits → 30 Hari",
        "btn_buy_vip": "💰 Beli VIP Coins",
        "btn_buy_star": "⭐ VIP Star (30 hari)",
        "btn_invite": "👥 Invite Friends",
        "btn_profile": "👤 My Profile",
        "btn_checkin": "✅ Daily Check-in",
        "btn_language": "🌐 Bahasa",
        "btn_support": "🆘 Support",
        "btn_back": "◀️ Back",
        "select_channel": (
            "🔄 **Pilih Verification Channel**\n\n"
            "🆓 Normal Channel - Free ({free_used}/{free_limit} slots/jam)\n"
            "⚡ VIP Channel - Instant (guna VIP Coins)\n"
            "⭐ Star Premium - Unlimited (MYR250/bulan)\n\n"
            "Baki anda:\n"
            "🔵 Credits: {credits}\n"
            "⚡ VIP Coins: {vip}\n"
            "⭐ Star: {star}\n"
        ),
        "star_active": "✅ Aktif sehingga {until}",
        "star_inactive": "❌ Tidak aktif",
        "need_credits": "❌ Maaf! Baki Credits anda tidak mencukupi.❌",
        "need_vip_coins": "❌ Maaf! Baki VIP Coins anda tidak mencukupi.",
        "free_full": "⚠️ Free channel sedang penuh ({free_used}/{free_limit} slots/jam). Sila cuba lagi atau guna VIP Coins.",
        "select_protocol": "🔧 Pilih protokol:",
        "proto_ssh": "SSH",
        "proto_vless": "VLESS",
        "proto_trojan": "Trojan",
        "creating": "⏳ Sedang create ID…",
        "created_ssh": (
            "✅ **SSH ID Berjaya Dibuat**\n\n"
            "Username: `{username}`\n"
            "Password: `{password}`\n"
            "Host: `{host}`\n"
            "Port: `22`\n"
            "Valid: **{days} hari**\n"
            "Expired: `{exp}`\n\n"
            "📌 Rules:\n{rules}"
        ),
        "created_uri": (
            "✅ **{proto} ID Berjaya Dibuat**\n\n"
            "{uri}\n\n"
            "Valid: **{days} hari**\n"
            "Expired: `{exp}`\n\n"
            "📌 Rules:\n{rules}"
        ),
        "rules_short": (
            "• Dilarang DDoS / flooding\n"
            "• Dilarang torrent / P2P\n"
            "• Dilarang abuse / hacking / spam\n"
            "• Dilarang multi login / share akaun\n"
            "• Langgar rules = ban (tiada refund)"
        ),
        "profile": (
            "👤 **Profil Anda**\n\n"
            "🆔 ID: `{user_id}`\n"
            "🔵 Credits: `{credits}` (free, limit {free_limit}/jam)\n"
            "⚡ VIP Coins: `{vip}` (1 coin setiap claim)\n"
            "⭐ Star: {star}\n"
            "👥 Referrals: `{refs}`\n"
            "✅ Claimed: `{claimed}`\n"
            "💵 Total Spent: `MYR{spent}`\n"
            "📅 Joined: `{joined}`\n"
        ),
        "invite": (
            "👥 **Invite Friends Program**\n\n"
            "Share referral link dan dapatkan kredit percuma!\n\n"
            "📋 Cara:\n"
            "1. Share link kepada kawan\n"
            "2. Mereka subscribe channel\n"
            "3. Setiap 3 kawan = 1 credit!\n\n"
            "⚠️ Maksimum 90 referrals. Lepas 90, tiada credit lagi.\n\n"
            "👥 Referrals anda: {refs}\n"
            "💳 Credits anda: {credits}\n\n"
            "🔗 Referral link:\n{link}\n\n"
            "💡 Terima kasih! Kos server tinggi."
        ),
        "checkin_ok": "✅ Check-in berjaya!\n💰 Dapat: +1 point\n💳 Jumlah point: {points}\n\n(Note: 30 points = 1 credit)",
        "checkin_already": "ℹ️ Anda sudah check-in hari ini. Datang semula esok!",
        "payment_warning": (
            "⚠️ **AMARAN PENTING:**\n\n"
            "Buka invoice tapi tak bayar akan direkod!\n"
            "Jika anda buka invoice tanpa bayar 3+ kali, akaun akan AUTO BLOCK.\n\n"
            "Teruskan hanya jika anda benar-benar mahu bayar.\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        ),
        "buy_vip_title": (
            "💰 **Beli VIP Coins**\n"
            "💳 Baki: {vip} VIP coins\n\n"
            "📦 Pilih pakej:"
        ),
        "buy_star_title": (
            "⭐ **VIP Star Subscription**\n\n"
            "💎 Harga: MYR250\n"
            "⏱ Tempoh: 30 hari\n\n"
            "Kelebihan:\n"
            "✅ UNLIMITED ID selama 30 hari\n"
            "✅ Tiada potongan credit setiap ID\n"
            "✅ VIP badge dalam profil\n\n"
            "Klik butang di bawah untuk beli:"
        ),
        "invoice_created": (
            "🧾 **Invoice Berjaya Dibuat**\n\n"
            "Jenis: {type}\n"
            "Jumlah: MYR{amount}\n\n"
            "➡️ Klik **Pay Now** untuk buka ToyyibPay.\n"
            "Lepas bayar, klik **Check Payment**.\n\n"
            "Invoice tamat dalam {mins} minit."
        ),
        "invoice_paid": "✅ Pembayaran diterima! Baki anda telah dikemaskini.",
        "invoice_pending": "⏳ Bayaran belum dikesan. Jika anda sudah bayar, tunggu 1-2 minit dan cuba lagi.",
        "invoice_expired": "❌ Invoice tamat / tidak dibayar.",
        "blocked_unpaid": "⛔ Anda buka invoice tanpa bayar 3 kali. Akaun anda telah diblock. Hubungi support.",
        "lang_choose": "🌐 Pilih bahasa:",
        "lang_ms": "Bahasa Melayu",
        "lang_en": "English",
        "lang_zh": "中文",
        "support_hint": "🆘 Untuk support, sila buka: @{support_bot}",
        "convert_info": (
            "♻️ **Convert Credits**\n\n"
            "💡 Contoh: 10 credits = ID 30 hari\n"
            "Convert ini untuk **SEMUA protokol**.\n\n"
            "Baki credits anda: {credits}"
        ),
        "convert_need": "❌ Maaf! Baki Credits anda tidak mencukupi. Perlu {need} credits.",
        "created_info": (
            "Valid: **{days} hari**\n"
            "Expired: `{exp}`\n\n"
            "📌 Rules:\n{rules}"
        ),

    },
    "zh": {
        "welcome": "👋 欢迎使用 Free VPN Generator！",
        "welcome_back": "👋 欢迎回来！",
        "subscribe_required": (
            "⚠️ 使用本机器人前，你需要先订阅我们的频道：\n\n"
            "1️⃣ 订阅下面所有频道\n"
            "2️⃣ 点击 '✅ 检查订阅'\n"
            "3️⃣ 获取机器人权限！\n\n"
            "💳 订阅后你将获得 **1 个免费积分**！"
        ),
        "subscription_ok": "✅ 感谢订阅！\n\n💳 你已获得 **1 个免费积分**！\n\n现在可以使用机器人。",
        "subscription_already_ok": "✅ 已验证订阅，可以使用机器人。",
        "subscription_fail": "❌ 你尚未订阅所有必需频道！\n\n请订阅全部频道后重试。",
        "agreement_required": (
            "📜 **需要同意用户协议**\n\n"
            "使用前请阅读并同意用户协议：\n"
            "👉 Read User Agreement\n\n"
            "点击 “I Accept” 即表示你已阅读并同意条款。\n\n"
            "⚠️ 未同意协议无法使用机器人。"
        ),
        "blocked": "⛔ 你的账号已被封禁，请联系支持。",
        "menu_choose": "请选择操作：",
        "btn_check_sub": "✅ 检查订阅",
        "btn_accept": "✅ I Accept",
        "btn_read_agreement": "👉 Read User Agreement",
        "btn_verify": "✅ Verify",
        "btn_convert": "♻️ 10积分→30天",
        "btn_buy_vip": "💰 购买 VIP Coins",
        "btn_buy_star": "⭐ VIP Star（30天）",
        "btn_invite": "👥 邀请好友",
        "btn_profile": "👤 个人资料",
        "btn_checkin": "✅ 每日签到",
        "btn_language": "🌐 语言",
        "btn_support": "🆘 客服",
        "btn_back": "◀️ 返回",
        "select_channel": (
            "🔄 **选择验证通道**\n\n"
            "🆓 普通通道 - 免费（{free_used}/{free_limit} 每小时名额）\n"
            "⚡ VIP 通道 - 快速（消耗 VIP Coins）\n"
            "⭐ Star Premium - 无限（MYR250/月）\n\n"
            "你的余额：\n"
            "🔵 Credits: {credits}\n"
            "⚡ VIP Coins: {vip}\n"
            "⭐ Star: {star}\n"
        ),
        "star_active": "✅ 有效至 {until}",
        "star_inactive": "❌ 未开通",
        "need_credits": "❌ 抱歉，你的 Credits 不足。",
        "need_vip_coins": "❌ 抱歉，你的 VIP Coins 不足。",
        "free_full": "⚠️ 免费通道已满（{free_used}/{free_limit}）。请稍后再试或使用 VIP Coins。",
        "select_protocol": "🔧 选择协议：",
        "proto_ssh": "SSH",
        "proto_vless": "VLESS",
        "proto_trojan": "Trojan",
        "creating": "⏳ 正在创建账号…",
        "created_ssh": (
            "✅ **SSH 账号已创建**\n\n"
            "Username: `{username}`\n"
            "Password: `{password}`\n"
            "Host: `{host}`\n"
            "Port: `22`\n"
            "有效期: **{days} 天**\n"
            "到期: `{exp}`\n\n"
            "📌 规则:\n{rules}"
        ),
        "created_uri": (
            "✅ **{proto} 账号已创建**\n\n"
            "{uri}\n\n"
            "有效期: **{days} 天**\n"
            "到期: `{exp}`\n\n"
            "📌 规则:\n{rules}"
        ),
        "rules_short": (
            "• 禁止 DDoS / 洪泛\n"
            "• 禁止 BT / P2P\n"
            "• 禁止 滥用 / 黑客 / 垃圾信息\n"
            "• 禁止 多设备同时登录/分享账号\n"
            "• 违规=封禁（不退款）"
        ),
        "profile": (
            "👤 **个人资料**\n\n"
            "🆔 ID: `{user_id}`\n"
            "🔵 Credits: `{credits}`（免费，每小时{free_limit}名额）\n"
            "⚡ VIP Coins: `{vip}`（每次领取1 coin）\n"
            "⭐ Star: {star}\n"
            "👥 邀请人数: `{refs}`\n"
            "✅ 已领取: `{claimed}`\n"
            "💵 总消费: `MYR{spent}`\n"
            "📅 注册日期: `{joined}`\n"
        ),
        "invite": (
            "👥 **邀请好友计划**\n\n"
            "分享邀请链接获取免费 Credits！\n\n"
            "📋 规则：\n"
            "1. 分享链接给好友\n"
            "2. 好友订阅频道\n"
            "3. 每 3 个好友 = 1 个 Credit\n\n"
            "⚠️ 最多统计 90 个邀请，超过后不再发放。\n\n"
            "👥 邀请人数: {refs}\n"
            "💳 Credits: {credits}\n\n"
            "🔗 邀请链接:\n{link}\n\n"
            "💡 感谢理解！服务器成本很高。"
        ),
        "checkin_ok": "✅ 签到成功！\n💰 获得：+1 point\n💳 当前 points：{points}\n\n（30 points = 1 credit）",
        "checkin_already": "ℹ️ 今天已签到，请明天再来！",
        "payment_warning": (
            "⚠️ **重要提醒：**\n\n"
            "创建付款账单但不付款会被记录！\n"
            "累计 3 次以上未付款，账号将自动封禁。\n\n"
            "仅在确定要付款时继续。\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        ),
        "buy_vip_title": (
            "💰 **购买 VIP Coins**\n"
            "💳 当前余额: {vip} VIP coins\n\n"
            "📦 选择套餐："
        ),
        "buy_star_title": (
            "⭐ **VIP Star 订阅**\n\n"
            "💎 价格: MYR250\n"
            "⏱ 时长: 30 天\n\n"
            "权益：\n"
            "✅ 30 天无限领取\n"
            "✅ 领取不扣 Credits\n"
            "✅ 资料显示 VIP 标识\n\n"
            "点击下方按钮购买："
        ),
        "invoice_created": (
            "🧾 **已创建账单**\n\n"
            "类型: {type}\n"
            "金额: MYR{amount}\n\n"
            "➡️ 点击 **Pay Now** 打开 ToyyibPay。\n"
            "付款后点击 **Check Payment**。\n\n"
            "账单 {mins} 分钟后过期。"
        ),
        "invoice_paid": "✅ 已收到付款，余额已更新。",
        "invoice_pending": "⏳ 暂未检测到付款。若已付款，请等待1-2分钟后重试。",
        "invoice_expired": "❌ 账单已过期/未付款。",
        "blocked_unpaid": "⛔ 你已累计 3 次未付款，账号已被封禁。请联系支持。",
        "lang_choose": "🌐 选择语言：",
        "lang_ms": "Bahasa Melayu",
        "lang_en": "English",
        "lang_zh": "中文",
        "support_hint": "🆘 客服机器人：@{support_bot}",
        "convert_info": (
            "♻️ **Credits 转换**\n\n"
            "💡 示例：10 credits = 30 天账号\n"
            "适用于 **所有协议**。\n\n"
            "你的 credits：{credits}"
        ),
        "convert_need": "❌ Credits 不足，需要 {need} credits。",
        "created_info": (
            "有效期: **{days} 天**\n"
            "到期: `{exp}`\n\n"
            "📌 规则:\n{rules}"
        ),

    },
}


def normalize_lang(lang: str | None) -> str:
    if not lang:
        return "ms"
    lang = lang.lower()
    if lang.startswith("zh"):
        return "zh"
    if lang.startswith("en"):
        return "en"
    return "ms"


def t(lang: str | None, key: str, **kwargs: Any) -> str:
    lang = normalize_lang(lang)
    # fallback order: lang -> en -> ms -> key
    msg = MESSAGES.get(lang, {}).get(key) or MESSAGES.get("en", {}).get(key) or MESSAGES.get("ms", {}).get(key) or key
    if kwargs:
        try:
            return msg.format(**kwargs)
        except Exception:
            return msg
    return msg
