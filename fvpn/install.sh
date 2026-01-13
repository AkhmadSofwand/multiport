\
#!/usr/bin/env bash
set -euo pipefail

if [[ "$(id -u)" != "0" ]]; then
  echo "Please run as root."
  exit 1
fi

APP_DIR="/opt/fvpn"
ENV_DIR="/etc/fvpn"

function prompt() {
  local var="$1"
  local label="$2"
  local def="${3:-}"
  local secret="${4:-0}"
  local val=""
  if [[ "$secret" == "1" ]]; then
    read -rsp "$label${def:+ [$def]}: " val
    echo
  else
    read -rp "$label${def:+ [$def]}: " val
  fi
  if [[ -z "$val" ]]; then
    val="$def"
  fi
  eval "$var=\"\$val\""
}

echo "========================================"
echo " FVPN Auto Installer (Manager / Worker)"
echo "========================================"
echo
echo "1) Install as MANAGER (main bot + support bot + callback api)"
echo "2) Install as WORKER (agent api only)"
echo "3) Install BOTH (manager + worker on same server) [not recommended]"
echo
read -rp "Select mode [1/2/3]: " MODE

echo
echo "[1/5] Installing dependencies..."
apt-get update -y
apt-get install -y python3 python3-venv python3-pip curl unzip rsync

echo
echo "[2/5] Deploying application to ${APP_DIR} ..."
mkdir -p "$APP_DIR"
rsync -a --delete --exclude "venv" --exclude "__pycache__" ./ "$APP_DIR/"

echo
echo "[3/5] Creating venv + installing python requirements..."
python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install --upgrade pip
"$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"

mkdir -p "$ENV_DIR"
chmod 700 "$ENV_DIR"

function install_systemd_unit() {
  local src="$1"
  local name="$2"
  cp "$APP_DIR/systemd/$src" "/etc/systemd/system/$name.service"
}

if [[ "$MODE" == "1" || "$MODE" == "3" ]]; then
  echo
  echo "[4/5] Configuring MANAGER env..."
  prompt MAIN_BOT_TOKEN "MAIN_BOT_TOKEN (from @BotFather)" "" 1
  prompt SUPPORT_BOT_TOKEN "SUPPORT_BOT_TOKEN (optional, leave empty to disable support bot)" "" 1
  prompt SUPPORT_BOT_USERNAME "SUPPORT_BOT_USERNAME (e.g. fvpngensupportbot)" "fvpngensupportbot" 0
  prompt ADMIN_ID "ADMIN_ID (your Telegram numeric ID)" ""
  prompt BOT_USERNAME "BOT_USERNAME (your main bot username)" "fvpngenebot"
  prompt REQUIRED_CHANNELS "REQUIRED_CHANNELS (comma separated) e.g. @connectifyvpninfo,@connectifyvpnstore" "@connectifyvpninfo,@connectifyvpnstore"
  prompt USER_AGREEMENT_URL "USER_AGREEMENT_URL (Telegraph link)" "https://telegra.ph/"

  echo
  echo "ToyyibPay (optional but recommended for VIP Coins & Star payment)"
  prompt TOYYIBPAY_ENABLED "TOYYIBPAY_ENABLED (true/false)" "true"
  prompt TOYYIBPAY_IS_SANDBOX "TOYYIBPAY_IS_SANDBOX (true/false)" "false"
  prompt TOYYIBPAY_USER_SECRET_KEY "TOYYIBPAY_USER_SECRET_KEY" "" 1
  prompt TOYYIBPAY_CATEGORY_CODE "TOYYIBPAY_CATEGORY_CODE" "" 0
  prompt TOYYIBPAY_RETURN_URL "TOYYIBPAY_RETURN_URL (after payment)" "https://t.me/${BOT_USERNAME}"
  prompt TOYYIBPAY_CALLBACK_URL "TOYYIBPAY_CALLBACK_URL (optional - your public callback endpoint)" ""

  prompt DB_PATH "DB_PATH" "/var/lib/fvpn-manager/manager.db"

  cat > "$ENV_DIR/fvpn.env" <<EOF
MAIN_BOT_TOKEN=${MAIN_BOT_TOKEN}
SUPPORT_BOT_TOKEN=${SUPPORT_BOT_TOKEN}
SUPPORT_BOT_USERNAME=${SUPPORT_BOT_USERNAME}
ADMIN_ID=${ADMIN_ID}
BOT_USERNAME=${BOT_USERNAME}
REQUIRED_CHANNELS=${REQUIRED_CHANNELS}
USER_AGREEMENT_URL=${USER_AGREEMENT_URL}

# Claim rules
FREE_SLOTS_PER_HOUR=20
FREE_CLAIM_COST_CREDITS=1
FREE_CLAIM_VALIDITY_DAYS=3

CONVERT_COST_CREDITS=10
CONVERT_VALIDITY_DAYS=30

VIP_CLAIM_COST_VIP_COINS=1
VIP_CLAIM_VALIDITY_DAYS=3

STAR_SUBSCRIPTION_DAYS=30

# ToyyibPay
TOYYIBPAY_ENABLED=${TOYYIBPAY_ENABLED}
TOYYIBPAY_IS_SANDBOX=${TOYYIBPAY_IS_SANDBOX}
TOYYIBPAY_USER_SECRET_KEY=${TOYYIBPAY_USER_SECRET_KEY}
TOYYIBPAY_CATEGORY_CODE=${TOYYIBPAY_CATEGORY_CODE}
TOYYIBPAY_RETURN_URL=${TOYYIBPAY_RETURN_URL}
TOYYIBPAY_CALLBACK_URL=${TOYYIBPAY_CALLBACK_URL}
INVOICE_EXPIRE_MINUTES=60

DB_PATH=${DB_PATH}

AGENT_TIMEOUT_SEC=15
SERVER_PING_TIMEOUT_SEC=5
EOF
  chmod 600 "$ENV_DIR/fvpn.env"

  echo
  echo "[4/5] Installing systemd units (manager)..."
  install_systemd_unit "fvpn-mainbot.service" "fvpn-mainbot"
  install_systemd_unit "fvpn-supportbot.service" "fvpn-supportbot"
  install_systemd_unit "fvpn-callback-api.service" "fvpn-callback-api"

  systemctl daemon-reload
  systemctl enable --now fvpn-mainbot
  if [[ -n "$SUPPORT_BOT_TOKEN" ]]; then
    systemctl enable --now fvpn-supportbot
  else
    echo "Support bot disabled (no SUPPORT_BOT_TOKEN)."
  fi
  systemctl enable --now fvpn-callback-api || true

  echo
  echo "✅ Manager installed."
  echo "Admin commands:"
  echo "  /addserver FREE name https://ip:7000 API_KEY 100"
  echo "  /addserver STAR name https://ip:7000 API_KEY 100"
  echo "  /servers"
fi

if [[ "$MODE" == "2" || "$MODE" == "3" ]]; then
  echo
  echo "[4/5] Configuring WORKER env..."
  prompt AGENT_API_KEY "AGENT_API_KEY (generate a strong random key)" "$(openssl rand -hex 16)"
  prompt AGENT_LISTEN_PORT "AGENT_LISTEN_PORT" "7000"
  prompt AGENT_MAX_USERS "AGENT_MAX_USERS (limit per server)" "100"
  prompt XRAY_DOMAIN_FILE "XRAY_DOMAIN_FILE" "/usr/local/etc/xray/domain"
  prompt PUBLIC_TLS_PORT "PUBLIC_TLS_PORT" "443"
  prompt XRAY_VLESS_TLS_CONFIG "XRAY_VLESS_TLS_CONFIG" "/usr/local/etc/xray/vless.json"
  prompt XRAY_VLESS_NONE_CONFIG "XRAY_VLESS_NONE_CONFIG" "/usr/local/etc/xray/vnone.json"
  prompt XRAY_TROJAN_TLS_CONFIG "XRAY_TROJAN_TLS_CONFIG" "/usr/local/etc/xray/trojanws.json"
  prompt VLESS_WS_PATH "VLESS_WS_PATH" "/vless"
  prompt TROJAN_WS_PATH "TROJAN_WS_PATH" "/trojan"
  prompt AGENT_DB_PATH "AGENT_DB_PATH" "/var/lib/fvpn-agent/agent.db"

  cat > "$ENV_DIR/fvpn-agent.env" <<EOF
AGENT_API_KEY=${AGENT_API_KEY}
AGENT_LISTEN_HOST=0.0.0.0
AGENT_LISTEN_PORT=${AGENT_LISTEN_PORT}
AGENT_MAX_USERS=${AGENT_MAX_USERS}
AGENT_DB_PATH=${AGENT_DB_PATH}

XRAY_DOMAIN_FILE=${XRAY_DOMAIN_FILE}
PUBLIC_TLS_PORT=${PUBLIC_TLS_PORT}
PUBLIC_NONTLS_PORT=80

XRAY_VLESS_TLS_CONFIG=${XRAY_VLESS_TLS_CONFIG}
XRAY_VLESS_NONE_CONFIG=${XRAY_VLESS_NONE_CONFIG}
XRAY_TROJAN_TLS_CONFIG=${XRAY_TROJAN_TLS_CONFIG}

VLESS_WS_PATH=${VLESS_WS_PATH}
TROJAN_WS_PATH=${TROJAN_WS_PATH}

RESTART_VLESS_SERVICE=xray@vless
RESTART_VLESS_NONE_SERVICE=xray@none
RESTART_TROJAN_SERVICE=xray@trojanws
EOF
  chmod 600 "$ENV_DIR/fvpn-agent.env"

  echo
  echo "[4/5] Installing systemd units (worker)..."
  install_systemd_unit "fvpn-agent.service" "fvpn-agent"
  systemctl daemon-reload
  systemctl enable --now fvpn-agent

  echo
  echo "✅ Worker installed."
  echo "AGENT API is now listening on port ${AGENT_LISTEN_PORT}."
  echo "Use this in manager: /addserver FREE|STAR name https://WORKER_IP:${AGENT_LISTEN_PORT} ${AGENT_API_KEY} ${AGENT_MAX_USERS}"
fi

echo
echo "[5/5] Installing panel command: fvpn-panel"
cp "$APP_DIR/panel.sh" /usr/local/bin/fvpn-panel
chmod +x /usr/local/bin/fvpn-panel

echo
echo "DONE ✅"
echo "Run: fvpn-panel"
