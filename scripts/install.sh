#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_SRC="$REPO_DIR/systemd/wingxtra-precision-landing.service"
SERVICE_DST="/etc/systemd/system/wingxtra-precision-landing.service"
DEFAULTS_FILE="/etc/default/wingxtra-precision-landing"

if [[ $EUID -ne 0 ]]; then
  echo "Please run as root: sudo ./scripts/install.sh"
  exit 1
fi

cd "$REPO_DIR"
python3 -m pip install -r requirements.txt

install -m 0644 "$SERVICE_SRC" "$SERVICE_DST"

if [[ ! -f "$DEFAULTS_FILE" ]]; then
  cat > "$DEFAULTS_FILE" <<'EODEF'
# Optional runtime args passed to scripts/run.sh
# Example:
# WINGXTRA_ARGS="--dry-run --debug-overlay --databus-host 127.0.0.1 --databus-port 60000"
WINGXTRA_ARGS=""
EODEF
  chmod 0644 "$DEFAULTS_FILE"
fi

systemctl daemon-reload
systemctl enable wingxtra-precision-landing.service

echo "Installed. Start service with: systemctl start wingxtra-precision-landing.service"
echo "Inspect logs with: journalctl -u wingxtra-precision-landing -f"
