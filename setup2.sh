#!/usr/bin/env bash
set -euo pipefail

# =========================
# Multiport + FVPN (Bot) installer wrapper
# Works on Ubuntu 22.04+ & Debian 12+
# =========================

if [[ "$(id -u)" != "0" ]]; then
  echo "Sila jalankan sebagai root."
  exit 1
fi

LOCKFILE="/var/lock/fvpn_multiport_setup.lock"
exec 9>"$LOCKFILE"
if ! flock -n 9; then
  echo "Installer sedang berjalan. Sila tunggu dan cuba lagi."
  exit 1
fi

REPO_URL="${REPO_URL:-https://github.com/AkhmadSofwand/multiport.git}"
REPO_DIR="${REPO_DIR:-/opt/multiport}"

export DEBIAN_FRONTEND=noninteractive

echo "========================================"
echo "  Multiport Installer (Ubuntu/Debian)"
echo "========================================"
echo
echo "[1/4] Install dependencies..."
apt-get update -y
apt-get install -y git curl wget ca-certificates unzip rsync python3

echo
echo "[2/4] Clone / update repo: $REPO_URL"
if [[ -d "$REPO_DIR/.git" ]]; then
  git -C "$REPO_DIR" fetch --all --prune
  git -C "$REPO_DIR" reset --hard origin/main || git -C "$REPO_DIR" reset --hard origin/master
else
  rm -rf "$REPO_DIR"
  git clone --depth 1 "$REPO_URL" "$REPO_DIR"
fi

echo
echo "[3/4] Install Multiport..."
bash "$REPO_DIR/setup-core.sh"

echo
echo "[4/4] Integrate Bot (FVPN) ke menu..."
# Pastikan command wujud (menu option 14/15 akan guna ini)
if [[ -f "$REPO_DIR/fvpn/install.sh" ]]; then
  install -m 0755 "$REPO_DIR/fvpn/install.sh" /usr/local/bin/fvpn-install
fi
if [[ -f "$REPO_DIR/fvpn/panel.sh" ]]; then
  install -m 0755 "$REPO_DIR/fvpn/panel.sh" /usr/local/bin/fvpn-panel
fi

echo
echo "=============================="
echo " Bot installer dah siap disediakan."
echo " • Untuk pasang bot: pilih [14] INSTALL BOT"
echo " • Untuk setting bot: pilih [15] SETTING BOT"
echo "=============================="
echo
echo "Selesai ✅"
