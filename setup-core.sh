#!/usr/bin/env bash
set -euo pipefail

if [[ "$(id -u)" != "0" ]]; then
  echo "Please run as root."
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export DEBIAN_FRONTEND=noninteractive

echo "========================================"
echo " Multiport Installer (Ubuntu 22.04+/Debian 12+ ready)"
echo "========================================"
echo

# Basic deps used across modules
apt-get update -y
apt-get install -y --no-install-recommends \
  curl wget ca-certificates gnupg lsb-release \
  iproute2 net-tools \
  unzip rsync \
  python3

# Run module installers (order matters for some deps)
bash "$SCRIPT_DIR/install/ssh-vpn.sh"
bash "$SCRIPT_DIR/install/ins-xray.sh"
bash "$SCRIPT_DIR/install/ohp.sh"
bash "$SCRIPT_DIR/install/ssr.sh"
bash "$SCRIPT_DIR/install/sodosok.sh"
bash "$SCRIPT_DIR/install/trojan-go.sh"
bash "$SCRIPT_DIR/install/wg.sh"

# Deploy menu command
install -m 0755 "$SCRIPT_DIR/menu.sh" /usr/bin/menu

# =====================
# BOT FVpn (Menu #14/#15)
# =====================
# Menu utama (menu.sh) dah ada pilihan:
#   [14] Install Bot  -> /usr/bin/install-bot
#   [15] Setting Bot  -> /usr/bin/set-bot
# Tetapi command tersebut tak akan wujud kalau script bot tak dipasang.
# Jadi kita pasang wrapper script bot sekali.
if [ -f "$SCRIPT_DIR/fvpn/install.sh" ]; then
  install -m 0755 "$SCRIPT_DIR/fvpn/install.sh" /usr/bin/install-bot
fi
if [ -f "$SCRIPT_DIR/fvpn/panel.sh" ]; then
  install -m 0755 "$SCRIPT_DIR/fvpn/panel.sh" /usr/bin/set-bot
fi

echo
echo "✅ Multiport siap."
echo "Taip: menu"
