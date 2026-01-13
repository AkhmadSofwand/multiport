\
#!/usr/bin/env bash
set -euo pipefail

SERVICES_MANAGER=("fvpn-mainbot" "fvpn-supportbot" "fvpn-callback-api")
SERVICES_WORKER=("fvpn-agent")

function header() {
  clear
  echo "========================================"
  echo "   FVPN PANEL (On/Off Services)"
  echo "========================================"
  echo
}

function status_services() {
  echo "---- Services status ----"
  for s in "${SERVICES_MANAGER[@]}"; do
    systemctl is-enabled "$s" >/dev/null 2>&1 && echo "[manager] $s: enabled" || true
    systemctl is-active "$s" >/dev/null 2>&1 && echo "[manager] $s: active" || echo "[manager] $s: inactive"
  done
  for s in "${SERVICES_WORKER[@]}"; do
    systemctl is-enabled "$s" >/dev/null 2>&1 && echo "[worker]  $s: enabled" || true
    systemctl is-active "$s" >/dev/null 2>&1 && echo "[worker]  $s: active" || echo "[worker]  $s: inactive"
  done
  echo
}

function do_action() {
  local action="$1"
  local svc="$2"
  systemctl "$action" "$svc"
  echo "✅ $action $svc"
  sleep 1
}

while true; do
  header
  status_services
  echo "1) Start manager services"
  echo "2) Stop manager services"
  echo "3) Restart manager services"
  echo "4) Start worker agent"
  echo "5) Stop worker agent"
  echo "6) Restart worker agent"
  echo "7) View logs (main bot)"
  echo "8) View logs (agent)"
  echo "0) Exit"
  echo
  read -rp "Select: " choice
  case "$choice" in
    1)
      for s in "${SERVICES_MANAGER[@]}"; do do_action start "$s"; done
      ;;
    2)
      for s in "${SERVICES_MANAGER[@]}"; do do_action stop "$s"; done
      ;;
    3)
      for s in "${SERVICES_MANAGER[@]}"; do do_action restart "$s"; done
      ;;
    4)
      do_action start "fvpn-agent"
      ;;
    5)
      do_action stop "fvpn-agent"
      ;;
    6)
      do_action restart "fvpn-agent"
      ;;
    7)
      journalctl -u fvpn-mainbot -n 100 --no-pager || true
      read -rp "Press enter to continue..." _
      ;;
    8)
      journalctl -u fvpn-agent -n 100 --no-pager || true
      read -rp "Press enter to continue..." _
      ;;
    0) exit 0 ;;
    *) echo "Invalid"; sleep 1 ;;
  esac
done
