#!/usr/bin/env bash
set -euo pipefail

if [[ "$(id -u)" != "0" ]]; then
  echo "Please run as root."
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_DIR="$(cd "$SCRIPT_DIR/../websocket-python" && pwd)"

echo "[WS] Installing dependencies..."
apt-get update -y
apt-get install -y python3

echo "[WS] Deploying websocket proxy scripts..."
install -d /usr/local/bin

install -m 0755 "$WS_DIR/ws-dropbear.py" /usr/local/bin/ws-dropbear
install -m 0755 "$WS_DIR/ws-ovpn.py" /usr/local/bin/ws-ovpn
install -m 0755 "$WS_DIR/ws-ssl.py" /usr/local/bin/ws-ssl

echo "[WS] Installing systemd units..."
install -m 0644 "$WS_DIR/ws-dropbear.service" /etc/systemd/system/ws-dropbear.service
install -m 0644 "$WS_DIR/ws-ovpn.service" /etc/systemd/system/ws-ovpn.service
install -m 0644 "$WS_DIR/ws-ssl.service" /etc/systemd/system/ws-ssl.service

systemctl daemon-reload

echo "[WS] Enabling + starting services..."
systemctl enable --now ws-dropbear ws-ovpn ws-ssl

echo "[WS] Done ✅"
