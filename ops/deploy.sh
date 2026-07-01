#!/usr/bin/env bash
#
# Safe production deploy for MH-02.
#
# Why this exists: deploying by hand is error-prone. Running plain
# `docker compose` (dev file), or in the foreground (Ctrl+C kills the site),
# has bitten us. This script always uses the prod compose file, runs detached,
# and syncs the code to exactly what's on origin/main.
#
# Usage (on the VPS):   bash /opt/mh02/ops/deploy.sh
#
set -euo pipefail

cd /opt/mh02

COMPOSE="docker compose -f docker-compose.prod.yml"

echo "==> Fetching latest code from origin/main ..."
git fetch origin
# Make the working tree exactly match origin/main. This discards any local
# edits to tracked files (prod should only ever run released code); untracked
# files/dirs like ops/ and backups are left untouched.
git reset --hard origin/main
echo "    now at: $(git log --oneline -1)"

echo "==> Rebuilding and restarting (detached) ..."
$COMPOSE up -d --build

echo "==> Waiting for the API to become healthy ..."
ok=""
for i in $(seq 1 20); do
  code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://localhost:8000/health || true)"
  if [ "$code" = "200" ]; then ok="yes"; echo "    api healthy."; break; fi
  sleep 3
done
[ -n "$ok" ] || echo "    WARNING: api did not report healthy within ~60s — check logs."

echo "==> Container status:"
$COMPOSE ps

echo "==> Done."
