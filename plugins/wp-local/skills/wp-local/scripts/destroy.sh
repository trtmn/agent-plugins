#!/usr/bin/env bash
set -euo pipefail

NAME="${1:-}"
CONFIRM="${2:-}"

if [ -z "$NAME" ]; then
    printf '{"ok":false,"message":"Usage: destroy.sh <site-name> <site-name-to-confirm>"}\n'
    exit 1
fi

SITE_DIR="$HOME/wordpress-sites/$NAME"
if [ ! -f "$SITE_DIR/docker-compose.yml" ]; then
    printf '{"ok":false,"name":"%s","message":"Site not found at %s"}\n' "$NAME" "$SITE_DIR"
    exit 1
fi

if [ "$CONFIRM" != "$NAME" ]; then
    printf '{"ok":false,"name":"%s","message":"Confirmation mismatch — pass the site name as both arguments to confirm destruction"}\n' "$NAME"
    exit 1
fi

cd "$SITE_DIR"
docker compose --project-name "$NAME" down --volumes --remove-orphans >/dev/null 2>&1 || true

cd "$HOME/wordpress-sites"
rm -rf "$SITE_DIR"

printf '{"ok":true,"name":"%s","message":"Site destroyed and all data permanently deleted"}\n' "$NAME"
