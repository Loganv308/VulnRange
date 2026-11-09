#!/usr/bin/env bash
# Generates .env with random flags (so you can't just read them from source), then builds and starts the range.
# Usage: ./setup.sh            -> bind to 127.0.0.1
#        BIND_IP=10.10.50.5 ./setup.sh   -> bind to a lab-VLAN interface
set -euo pipefail
cd "$(dirname "$0")"

FLAGS=(FLAG_BANK_SQLI_LOGIN FLAG_BANK_SQLI_UNION FLAG_BANK_IDOR FLAG_BANK_LOGIC FLAG_BANK_SSTI
       FLAG_DEV_JWT FLAG_DEV_FILE FLAG_SSRF FLAG_FS_LFI FLAG_FS_RCE)

if [[ ! -f .env || "${1:-}" == "--reset" ]]; then
  : > .env
  echo "BIND_IP=${BIND_IP:-127.0.0.1}" >> .env
  for f in "${FLAGS[@]}"; do
    echo "$f=FLAG{$(head -c 12 /dev/urandom | od -An -tx1 | tr -d ' \n')}" >> .env
  done
  chmod 600 .env
  echo "[+] Generated .env with fresh flags (don't peek -- use ./check_flag.py)"
fi

docker compose up -d --build
echo
echo "[+] BrokenBank  -> http://${BIND_IP:-127.0.0.1}:8001"
echo "[+] DevPortal   -> http://${BIND_IP:-127.0.0.1}:8002"
echo "[+] FileShare   -> http://${BIND_IP:-127.0.0.1}:8003"
echo "[i] Reset everything: docker compose down -v && ./setup.sh --reset"
