#!/usr/bin/env bash
set -euo pipefail

# ==========================================================
# FVPN + MULTIPORT One-Step Installer (No tar.gz required)
# Repo: https://github.com/AkhmadSofwand/multiport
# This script will:
#   1) Install MULTIPORT VPN (upstream setup2.sh)
#   2) Clone your repo and install FVPN WORKER agent from /fvpn
# ==========================================================

# ===== CONFIG =====
UPSTREAM_MULTIPORT_SETUP_URL="https://raw.githubusercontent.com/KhaiVpn767/multiport/main/setup2.sh"

# Repo kau (public)
FVPN_REPO_GIT="https://github.com/AkhmadSofwand/multiport.git"
FVPN_SUBDIR="fvpn"            # folder bot/agent dalam repo
FVPN_SRC_DIR="/opt/fvpn-src"  # tempat clone repo (boleh tukar)

# Agent defaults (boleh override: export AGENT_PORT=7000)
AGENT_PORT="${AGENT_PORT:-7000}"
AGENT_MAX_USERS="${AGENT_MAX_USERS:-100}"
PUBLIC_TLS_PORT="${PUBLIC_TLS_PORT:-443}"

# Optional security: allow agent port only from manager IP
# contoh: export MANAGER_IP="1.2.3.4"
MANAGER_IP="${MANAGER_IP:-}"

log(){ echo -e "\n[+] $*"; }
die(){ echo -e "\n[!] ERROR: $*" >&2; exit 1; }

need_root(){
  [[ "$(id -u)" == "0" ]] || die "Sila run sebagai root."
}

detect_xray_paths(){
  # Default multiport paths
  XRAY_DOMAIN_FILE="/usr/local/etc/xray/domain"
  XRAY_VLESS_TLS_CONFIG="/usr/local/etc/xray/vless.json"
  XRAY_VLESS_NONE_CONFIG="/usr/local/etc/xray/vnone.json"
  XRAY_TROJAN_TLS_CONFIG="/usr/local/etc/xray/trojanws.json"

  # fallback search
  if [[ ! -f "$XRAY_DOMAIN_FILE" ]]; then
    for p in /etc/xray/domain /usr/local/etc/xray/domain /etc/v2ray/domain; do
      [[ -f "$p" ]] && XRAY_DOMAIN_FILE="$p" && break
    done
  fi

  echo "$XRAY_DOMAIN_FILE|$XRAY_VLESS_TLS_CONFIG|$XRAY_VLESS_NONE_CONFIG|$XRAY_TROJAN_TLS_CONFIG"
}

install_deps(){
  log "Install dependencies"
  apt-get update -y
  apt-get install -y \
    bzip2 gzip coreutils screen curl wget unzip rsync \
    python3 python3-venv python3-pip openssl git ufw
}

install_multiport(){
  log "Install MULTIPORT VPN (upstream setup2.sh)"
  cd /root
  wget -O setup2_upstream.sh "$UPSTREAM_MULTIPORT_SETUP_URL"
  chmod +x setup2_upstream.sh
  ./setup2_upstream.sh
}

clone_repo(){
  log "Clone repo FVPN (tanpa tar.gz): $FVPN_REPO_GIT"
  rm -rf "$FVPN_SRC_DIR" || true
  mkdir -p "$(dirname "$FVPN_SRC_DIR")"
  git clone --depth 1 "$FVPN_REPO_GIT" "$FVPN_SRC_DIR"
  [[ -d "$FVPN_SRC_DIR/$FVPN_SUBDIR" ]] || die "Tak jumpa folder '$FVPN_SUBDIR' dalam repo."
  [[ -f "$FVPN_SRC_DIR/$FVPN_SUBDIR/install.sh" ]] || die "Tak jumpa '$FVPN_SUBDIR/install.sh'."
}

install_worker_agent(){
  log "Install FVPN WORKER agent dari $FVPN_SRC_DIR/$FVPN_SUBDIR"
  cd "$FVPN_SRC_DIR/$FVPN_SUBDIR"
  chmod +x install.sh

  IFS='|' read -r XRAY_DOMAIN_FILE XRAY_VLESS_TLS_CONFIG XRAY_VLESS_NONE_CONFIG XRAY_TROJAN_TLS_CONFIG < <(detect_xray_paths)

  if [[ ! -f "$XRAY_DOMAIN_FILE" ]]; then
    echo "[!] WARNING: domain file tak jumpa. Pastikan domain wujud. (Default: /usr/local/etc/xray/domain)"
  fi
  if [[ ! -f "$XRAY_VLESS_TLS_CONFIG" ]]; then
    echo "[!] WARNING: vless.json tak jumpa di $XRAY_VLESS_TLS_CONFIG"
  fi
  if [[ ! -f "$XRAY_TROJAN_TLS_CONFIG" ]]; then
    echo "[!] WARNING: trojanws.json tak jumpa di $XRAY_TROJAN_TLS_CONFIG"
  fi

  AGENT_API_KEY="$(openssl rand -hex 16)"
  AGENT_DB_PATH="/var/lib/fvpn-agent/agent.db"
  VLESS_WS_PATH="/vless"
  TROJAN_WS_PATH="/trojan"

  # Feed jawapan installer (MODE=2 Worker)
  # Urutan prompt ikut install.sh (WORKER):
  # mode, api_key, port, max_users, domain_file, tls_port, vless_tls, vless_none, trojan_tls, vless_path, trojan_path, db_path
  printf "2\n%s\n%s\n%s\n%s\n%s\n%s\n%s\n%s\n%s\n%s\n%s\n" \
    "$AGENT_API_KEY" \
    "$AGENT_PORT" \
    "$AGENT_MAX_USERS" \
    "$XRAY_DOMAIN_FILE" \
    "$PUBLIC_TLS_PORT" \
    "$XRAY_VLESS_TLS_CONFIG" \
    "$XRAY_VLESS_NONE_CONFIG" \
    "$XRAY_TROJAN_TLS_CONFIG" \
    "$VLESS_WS_PATH" \
    "$TROJAN_WS_PATH" \
    "$AGENT_DB_PATH" | bash ./install.sh

  log "Firewall rule for agent port ($AGENT_PORT)"
  if [[ -n "$MANAGER_IP" ]]; then
    ufw allow from "$MANAGER_IP" to any port "$AGENT_PORT" proto tcp || true
    ufw deny "$AGENT_PORT"/tcp || true
    echo "[+] UFW: allow only MANAGER_IP=$MANAGER_IP to port $AGENT_PORT"
  else
    ufw allow "$AGENT_PORT"/tcp || true
    echo "[!] UFW: port $AGENT_PORT dibuka umum. RECOMMEND set MANAGER_IP."
  fi
  ufw --force enable || true

  WORKER_IP="$(curl -fsSL ifconfig.me || true)"
  DOMAIN="$(cat "$XRAY_DOMAIN_FILE" 2>/dev/null || true)"

  log "DONE ✅ Worker siap."
  echo "--------------------------------------------------"
  echo "AGENT_API_KEY: $AGENT_API_KEY"
  echo "AGENT_PORT   : $AGENT_PORT"
  echo "MAX_USERS    : $AGENT_MAX_USERS"
  echo "DOMAIN       : ${DOMAIN:-UNKNOWN}"
  echo "PUBLIC IP    : ${WORKER_IP:-UNKNOWN}"
  echo "--------------------------------------------------"
  echo "PASTE dekat Telegram (admin) untuk register server:"
  echo
  echo "  /addserver FREE free1 https://${WORKER_IP:-WORKER_IP}:${AGENT_PORT} ${AGENT_API_KEY} ${AGENT_MAX_USERS}"
  echo "  /addserver STAR star1 https://${WORKER_IP:-WORKER_IP}:${AGENT_PORT} ${AGENT_API_KEY} ${AGENT_MAX_USERS}"
  echo
  echo "NOTE: FREE pool = free/vip/convert. STAR pool = VIP Star."
  echo "--------------------------------------------------"
}

main(){
  need_root

  log "Disable IPv6 + update"
  sysctl -w net.ipv6.conf.all.disable_ipv6=1 || true
  sysctl -w net.ipv6.conf.default.disable_ipv6=1 || true

  install_deps
  install_multiport
  clone_repo
  install_worker_agent
}

main "$@"