#!/usr/bin/env bash
# job-radar runner: loads config.env (if present) and runs the digest. Used by cron.
set -euo pipefail
cd "$(dirname "$0")"
if [ -f config.env ]; then
  set -a; . ./config.env; set +a
fi
exec python3 radar.py
