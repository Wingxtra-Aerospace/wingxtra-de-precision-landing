#!/usr/bin/env bash
# Native Debian/Raspberry Pi installation, not needed for the BlueOS container.
set -euo pipefail
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ $EUID -ne 0 || "$REPO_DIR" != /opt/wingxtra-de-precision-landing ]]; then
  echo 'Clone to /opt/wingxtra-de-precision-landing and run: sudo ./scripts/install.sh'
  exit 1
fi
apt-get update
apt-get install -y python3-venv python3-opencv python3-dev build-essential libxml2-dev libxslt1-dev
id wingxtra-pl >/dev/null 2>&1 || useradd --system --home-dir /var/lib/wingxtra-precision-landing --shell /usr/sbin/nologin wingxtra-pl
usermod -a -G video wingxtra-pl
if getent group render >/dev/null; then usermod -a -G render wingxtra-pl; fi
install -d -o wingxtra-pl -g wingxtra-pl -m 0750 /var/lib/wingxtra-precision-landing
python3 -m venv --system-site-packages "$REPO_DIR/.venv"
"$REPO_DIR/.venv/bin/pip" install --constraint "$REPO_DIR/docker-constraints.txt" "$REPO_DIR"
install -m 0644 "$REPO_DIR/systemd/wingxtra-precision-landing.service" /etc/systemd/system/wingxtra-precision-landing.service
systemctl daemon-reload
systemctl enable wingxtra-precision-landing.service
echo 'Installed with output stopped by default. Start: sudo systemctl start wingxtra-precision-landing'
