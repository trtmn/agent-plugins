#!/usr/bin/env bash
set -euo pipefail

NAME="${1:-}"
if [ -z "$NAME" ]; then
    printf '{"ok":false,"message":"Usage: start.sh <site-name>"}\n'
    exit 1
fi

SITE_DIR="$HOME/wordpress-sites/$NAME"
if [ ! -f "$SITE_DIR/docker-compose.yml" ]; then
    printf '{"ok":false,"name":"%s","message":"Site not found at %s"}\n' "$NAME" "$SITE_DIR"
    exit 1
fi

cd "$SITE_DIR"
docker compose --project-name "$NAME" start >/dev/null 2>&1

PORT=""
[ -f .env ] && PORT=$(grep '^WP_PORT=' .env 2>/dev/null | cut -d= -f2 || true)

printf '{"ok":true,"name":"%s","url":"http://localhost:%s","message":"Site started"}\n' "$NAME" "$PORT"
