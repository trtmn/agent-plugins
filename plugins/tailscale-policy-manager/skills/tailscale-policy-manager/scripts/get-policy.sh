#!/bin/bash
# Fetches the current Tailscale policy and prints to stdout as HuJSON
# Usage: TS_API_KEY=tskey-api-xxx TS_TAILNET=example.com ./get-policy.sh > policy.hujson

set -e

TAILNET="${TS_TAILNET:--}"
TOKEN="${TS_API_KEY}"

if [[ -z "$TOKEN" ]]; then
  echo "ERROR: TS_API_KEY must be set" >&2
  exit 1
fi

curl -s \
  -u "${TOKEN}:" \
  -H "Accept: application/hujson" \
  "https://api.tailscale.com/api/v2/tailnet/${TAILNET}/acl"
