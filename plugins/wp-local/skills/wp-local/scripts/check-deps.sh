#!/usr/bin/env bash
set -euo pipefail

errors=()
docker_ok=false
compose_ok=false

if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
    docker_ok=true
else
    errors+=("Docker is not installed or not running. Install Docker Desktop: https://docs.docker.com/get-docker/")
fi

if docker compose version &>/dev/null 2>&1; then
    compose_ok=true
else
    errors+=("Docker Compose plugin not found. It ships with Docker Desktop — ensure Docker Desktop is up to date.")
fi

ok=true
[ ${#errors[@]} -gt 0 ] && ok=false

errors_json="["
for i in "${!errors[@]}"; do
    errors_json+="\"${errors[$i]}\""
    [ "$i" -lt $((${#errors[@]} - 1)) ] && errors_json+=","
done
errors_json+="]"

printf '{"ok":%s,"docker":%s,"compose":%s,"errors":%s}\n' \
    "$ok" "$docker_ok" "$compose_ok" "$errors_json"
