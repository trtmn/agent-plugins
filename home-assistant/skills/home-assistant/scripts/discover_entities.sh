#!/usr/bin/env bash
# Discover Home Assistant entities grouped by domain
# Usage: discover_entities.sh [domain_filter]
# Examples:
#   discover_entities.sh          # all entities
#   discover_entities.sh light    # only lights
#   discover_entities.sh sensor   # only sensors

set -euo pipefail

# Load config
if [[ -f ~/.config/home-assistant/.env ]]; then
    source ~/.config/home-assistant/.env
fi

if [[ -z "${HA_URL:-}" || -z "${HA_TOKEN:-}" ]]; then
    echo "Error: HA_URL and HA_TOKEN must be set."
    echo "Run: source ~/.config/home-assistant/.env"
    exit 1
fi

DOMAIN_FILTER="${1:-}"

# Fetch all states
RESPONSE=$(curl -s -H "Authorization: Bearer $HA_TOKEN" \
    -H "Content-Type: application/json" \
    "$HA_URL/api/states")

if echo "$RESPONSE" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
    echo "$RESPONSE" | python3 -c "
import sys, json

data = json.load(sys.stdin)
domain_filter = '${DOMAIN_FILTER}'

# Group by domain
domains = {}
for entity in data:
    eid = entity['entity_id']
    domain = eid.split('.')[0]
    if domain_filter and domain != domain_filter:
        continue
    if domain not in domains:
        domains[domain] = []
    friendly_name = entity.get('attributes', {}).get('friendly_name', '')
    state = entity.get('state', 'unknown')
    domains[domain].append((eid, friendly_name, state))

if not domains:
    if domain_filter:
        print(f'No entities found for domain: {domain_filter}')
    else:
        print('No entities found.')
    sys.exit(0)

# Sort domains alphabetically
for domain in sorted(domains.keys()):
    entities = sorted(domains[domain], key=lambda x: x[0])
    print(f'\n=== {domain.upper()} ({len(entities)}) ===')
    for eid, name, state in entities:
        name_part = f' ({name})' if name else ''
        print(f'  {eid}{name_part}: {state}')

print(f'\nTotal: {sum(len(v) for v in domains.values())} entities across {len(domains)} domains')
"
else
    echo "Error: Failed to parse response from Home Assistant."
    echo "Response: $RESPONSE"
    exit 1
fi
