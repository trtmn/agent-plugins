#!/bin/bash
# Validates a Tailscale policy file against the API (no changes applied)
# Usage: TS_API_KEY=tskey-api-xxx TS_TAILNET=example.com ./validate-policy.sh [policy.hujson]

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

echo "Validating: $POLICY_FILE" >&2

RESULT=$(curl -s \
  -w "\n%{http_code}" \
  -u "${TOKEN}:" \
  -H "Content-Type: application/hujson" \
  --data-binary "@${POLICY_FILE}" \
  "https://api.tailscale.com/api/v2/tailnet/${TAILNET}/acl/validate")

HTTP_STATUS=$(echo "$RESULT" | tail -1)
BODY=$(echo "$RESULT" | sed '$d')

if [[ "$HTTP_STATUS" == "200" && "$BODY" == "{}" ]]; then
  echo "OK — policy is valid and all tests pass" >&2
  exit 0
else
  echo "FAILED (HTTP $HTTP_STATUS):" >&2
  echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
  exit 1
fi
