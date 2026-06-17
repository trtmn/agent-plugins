#!/usr/bin/env bash
set -euo pipefail

SITES_DIR="$HOME/wordpress-sites"

if [ ! -d "$SITES_DIR" ]; then
    echo "[]"
    exit 0
fi

sites=()
for site_dir in "$SITES_DIR"/*/; do
    [ -d "$site_dir" ] || continue
    [ -f "$site_dir/docker-compose.yml" ] || continue

    name=$(basename "$site_dir")
    port="null"
    status="unknown"

    if [ -f "$site_dir/.env" ]; then
        raw_port=$(grep '^WP_PORT=' "$site_dir/.env" 2>/dev/null | cut -d= -f2 || true)
        [ -n "$raw_port" ] && port="$raw_port"
    fi

    container_name="${name}-wordpress-1"
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${container_name}$"; then
        status="running"
    elif docker ps -a --format '{{.Names}}' 2>/dev/null | grep -q "^${container_name}$"; then
        status="stopped"
    fi

    sites+=("{\"name\":\"${name}\",\"path\":\"${site_dir%/}\",\"port\":${port},\"status\":\"${status}\"}")
done

if [ ${#sites[@]} -eq 0 ]; then
    echo "[]"
    exit 0
fi

result="["
for i in "${!sites[@]}"; do
    result+="${sites[$i]}"
    [ "$i" -lt $((${#sites[@]} - 1)) ] && result+=","
done
result+="]"

echo "$result"
