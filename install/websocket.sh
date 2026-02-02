#!/usr/bin/env bash
set -euo pipefail

if [[ "$(id -u)" != "0" ]]; then
  echo "[WS] Please run as root."
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_DIR="$(cd "$SCRIPT_DIR/../websocket-python" && pwd)"

echo "[WS] Installing dependencies..."
apt-get update -y
apt-get install -y python3

echo "[WS] Deploying websocket proxy scripts (cdn-* for menu compatibility)..."
install -d /usr/local/bin

# Keep legacy names expected by existing menu/status checks
install -m 0755 "$WS_DIR/cdn-dropbear.py" /usr/local/bin/cdn-dropbear
install -m 0755 "$WS_DIR/cdn-ssl.py"      /usr/local/bin/cdn-ssl
install -m 0755 "$WS_DIR/cdn-ovpn.py"     /usr/local/bin/cdn-ovpn

echo "[WS] Installing systemd units (cdn-*)..."
install -m 0644 "$WS_DIR/cdn-dropbear.service" /etc/systemd/system/cdn-dropbear.service
install -m 0644 "$WS_DIR/cdn-ssl.service"      /etc/systemd/system/cdn-ssl.service
install -m 0644 "$WS_DIR/cdn-ovpn.service"     /etc/systemd/system/cdn-ovpn.service

systemctl daemon-reload

echo "[WS] Enabling and starting services..."
systemctl enable --now cdn-dropbear cdn-ssl cdn-ovpn

echo "[WS] Done."
