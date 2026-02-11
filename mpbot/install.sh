#!/usr/bin/env bash
set -euo pipefail

log(){ echo -e "[MPBOT] $*"; }
die(){ echo -e "[MPBOT][ERROR] $*" >&2; exit 1; }

[[ "$(id -u)" == "0" ]] || die "Sila run sebagai root"

ADMIN_ID_DEFAULT="${MPBOT_ADMIN_ID:-8318635752}"
INSTALL_DIR="/opt/mpbot"
DATA_DIR="/var/lib/mpbot"
CONFIG_DIR="/etc/mpbot"
CONFIG_FILE="${CONFIG_DIR}/config.json"
VENV_DIR="${INSTALL_DIR}/venv"

log "Install dependencies (python3-venv, build tools)"
apt-get update -y
apt-get install -y python3 python3-venv python3-pip git curl

log "Deploy files ke ${INSTALL_DIR}"
rm -rf "${INSTALL_DIR}"
mkdir -p "${INSTALL_DIR}"
cp -a "$(dirname "$0")"/* "${INSTALL_DIR}/"

log "Setup venv"
python3 -m venv "${VENV_DIR}"
"${VENV_DIR}/bin/pip" install --upgrade pip wheel
"${VENV_DIR}/bin/pip" install -r "${INSTALL_DIR}/requirements.txt"

log "Setup data + config"
mkdir -p "${DATA_DIR}" "${CONFIG_DIR}"
chmod 700 "${DATA_DIR}" "${CONFIG_DIR}"

if [[ ! -f "${CONFIG_FILE}" ]]; then
  cat > "${CONFIG_FILE}" <<JSON
{
  "token": "",
  "admin_id": ${ADMIN_ID_DEFAULT},
  "db_path": "${DATA_DIR}/mpbot.db",
  "toyyibpay": {
    "enabled": false,
    "sandbox": false,
    "secret_key": "",
    "category_code": "",
    "return_url": "",
    "callback_url": ""
  }
}
JSON
  chmod 600 "${CONFIG_FILE}"
  log "Config dibuat: ${CONFIG_FILE} (SILA isi token bot Telegram)"
else
  log "Config sedia ada dijumpai: ${CONFIG_FILE} (tak diubah)"
fi

log "Install systemd services"
cat > /etc/systemd/system/mpbot.service <<UNIT
[Unit]
Description=Multiport Telegram Bot (MPBOT)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=${INSTALL_DIR}
Environment=MPBOT_CONFIG=${CONFIG_FILE}
ExecStart=${VENV_DIR}/bin/python -m mpbot.bot
Restart=always
RestartSec=3

# run as root supaya boleh create/renew akaun vpn
User=root

[Install]
WantedBy=multi-user.target
UNIT

cat > /etc/systemd/system/mpbot-api.service <<UNIT
[Unit]
Description=MPBOT ToyyibPay Callback API
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=${INSTALL_DIR}
Environment=MPBOT_CONFIG=${CONFIG_FILE}
ExecStart=${VENV_DIR}/bin/uvicorn mpbot.api:app --host 0.0.0.0 --port 8899
Restart=always
RestartSec=3
User=root

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable --now mpbot-api.service
systemctl enable --now mpbot.service

log "DONE ✅"
echo "----------------------------------------------------------------"
echo "1) Letak TOKEN bot Telegram dalam: ${CONFIG_FILE}"
echo "2) Callback API: http://<IP-VPS>:8899/toyyibpay/callback"
echo "3) Lepas set token, restart: systemctl restart mpbot"
echo "----------------------------------------------------------------"
