#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

# Optional overrides via /etc/default/wingxtra-precision-landing
EXTRA_ARGS="${WINGXTRA_ARGS:-}"

exec python3 -m src.wingxtra_pl.main ${EXTRA_ARGS}
