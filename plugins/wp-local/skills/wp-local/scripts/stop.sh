#!/usr/bin/env bash
set -euo pipefail

NAME="${1:-}"
if [ -z "$NAME" ]; then
    printf '{"ok":false,"message":"Usage: stop.sh <site-name>"}\n'
    exit 1
fi

SITE_DIR="$HOME/wordpress-sites/$NAME"
if [ ! -f "$SITE_DIR/docker-compose.yml" ]; then
    printf '{"ok":false,"name":"%s","message":"Site not found at %s"}\n' "$NAME" "$SITE_DIR"
    exit 1
fi

cd "$SITE_DIR"
docker compose --project-name "$NAME" stop >/dev/null 2>&1

printf '{"ok":true,"name":"%s","message":"Site stopped"}\n' "$NAME"
