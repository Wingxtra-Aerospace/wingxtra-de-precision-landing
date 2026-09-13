#!/usr/bin/env bash
set -euo pipefail
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec "$REPO_DIR/.venv/bin/wingxtra-pl" --data-dir "${PL_DATA_DIR:-/var/lib/wingxtra-precision-landing}" "$@"
