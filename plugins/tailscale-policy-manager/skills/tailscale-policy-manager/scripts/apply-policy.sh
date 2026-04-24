#!/bin/bash
# Validates then applies a Tailscale policy file using ETag-safe update
# Usage: TS_API_KEY=tskey-api-xxx TS_TAILNET=example.com ./apply-policy.sh [policy.hujson]

set -e

TAILNET="${TS_TAILNET:--}"
TOKEN="${TS_API_KEY}"
POLICY_FILE="${1:-policy.hujson}"

if [[ -z "$TOKEN" ]]; then
  echo "ERROR: TS_API_KEY must be set" >&2
  exit 1
fi

if [[ ! -f "$POLICY_FILE" ]]; then
  echo "ERROR: Policy file not found: $POLICY_FILE" >&2
  exit 1
fi

# Step 1: Validate
echo "Validating policy..." >&2
VALIDATE=$(curl -s \
  -u "${TOKEN}:" \
  -H "Content-Type: application/hujson" \
  --data-binary "@${POLICY_FILE}" \
  "https://api.tailscale.com/api/v2/tailnet/${TAILNET}/acl/validate")

if [[ "$VALIDATE" != "{}" ]]; then
  echo "Validation failed — aborting:" >&2
  echo "$VALIDATE" | python3 -m json.tool 2>/dev/null || echo "$VALIDATE"
  exit 1
fi

echo "Validation passed. Fetching current ETag..." >&2

# Step 2: Get ETag for safe apply
RESPONSE=$(curl -si \
  -u "${TOKEN}:" \
  -H "Accept: application/hujson" \
  "https://api.tailscale.com/api/v2/tailnet/${TAILNET}/acl")

ETAG=$(echo "$RESPONSE" | grep -i "^etag:" | awk '{print $2}' | tr -d '\r\n"')

echo "Applying policy (ETag: ${ETAG})..." >&2

# Step 3: Apply with ETag collision detection
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST \
  -u "${TOKEN}:" \
  -H "Content-Type: application/hujson" \
  -H "If-Match: \"${ETAG}\"" \
  --data-binary "@${POLICY_FILE}" \
  "https://api.tailscale.com/api/v2/tailnet/${TAILNET}/acl")

case "$HTTP_STATUS" in
  200) echo "Applied successfully." >&2 ;;
  412) echo "ERROR: Policy was modified by someone else since you fetched it. Pull the latest and retry." >&2; exit 1 ;;
  *)   echo "ERROR: Unexpected HTTP status $HTTP_STATUS" >&2; exit 1 ;;
esac
