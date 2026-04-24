# Tailscale API Reference

For when you need to interact with the policy API directly — validation scripts, custom deployment pipelines, or fetching the current policy.

## Base URL

```
https://api.tailscale.com/api/v2
```

## Authentication

### API key

```bash
curl -u "tskey-api-xxxxx:" \
  https://api.tailscale.com/api/v2/tailnet/-/acl
```

The colon means empty password (HTTP Basic Auth). API keys max out at 90 days.

### OAuth client credentials

```bash
# Step 1: Exchange credentials for a short-lived token (valid 1 hour)
TOKEN=$(curl -s \
  -d "client_id=tskey-client-xxxxx&client_secret=tskey-secret-xxxxx&grant_type=client_credentials" \
  https://api.tailscale.com/api/v2/oauth/token | jq -r .access_token)

# Step 2: Use as a Bearer token
curl -H "Authorization: Bearer $TOKEN" \
  https://api.tailscale.com/api/v2/tailnet/-/acl
```

Create OAuth clients at **Settings > Trust credentials > OAuth clients**. Scope to `policy_file` only.

### Tailnet name vs "-"

You can use `-` as a shorthand for your default tailnet:
```
/api/v2/tailnet/-/acl
/api/v2/tailnet/example.com/acl  # explicit
```

---

## GET — retrieve current policy

```bash
# Returns HuJSON (with comments preserved)
curl -u "tskey-api-xxxxx:" \
  -H "Accept: application/hujson" \
  https://api.tailscale.com/api/v2/tailnet/-/acl

# Returns standard JSON
curl -u "tskey-api-xxxxx:" \
  -H "Accept: application/json" \
  https://api.tailscale.com/api/v2/tailnet/-/acl
```

The response includes an **ETag header** — save this for safe updates.

---

## POST — apply new policy

```bash
# Replace entire policy file
curl -X POST \
  -u "tskey-api-xxxxx:" \
  -H "Content-Type: application/hujson" \
  --data-binary "@policy.hujson" \
  https://api.tailscale.com/api/v2/tailnet/-/acl
```

### Safe update with ETag (prevents overwriting concurrent changes)

```bash
# First get the current ETag
ETAG=$(curl -si -u "tskey-api-xxxxx:" \
  -H "Accept: application/hujson" \
  https://api.tailscale.com/api/v2/tailnet/-/acl | \
  grep -i "^etag:" | awk '{print $2}' | tr -d '\r')

# Then update, passing the ETag — returns HTTP 412 if someone else modified first
curl -X POST \
  -u "tskey-api-xxxxx:" \
  -H "Content-Type: application/hujson" \
  -H "If-Match: ${ETAG}" \
  --data-binary "@policy.hujson" \
  https://api.tailscale.com/api/v2/tailnet/-/acl
```

---

## POST — validate only (no changes applied)

The validate endpoint tests syntax and runs your `tests` block without modifying anything:

```bash
RESULT=$(curl -s \
  -u "tskey-api-xxxxx:" \
  -H "Content-Type: application/hujson" \
  --data-binary "@policy.hujson" \
  https://api.tailscale.com/api/v2/tailnet/-/acl/validate)

if [[ "$RESULT" == "{}" ]]; then
  echo "Valid!"
else
  echo "Failed: $RESULT"
fi
```

Returns `{}` on success, or a JSON error message on failure.

---

## Reusable scripts

### validate-policy.sh

```bash
#!/bin/bash
# Validates a policy file against the Tailscale API
# Usage: TS_API_KEY=tskey-api-xxx TS_TAILNET=example.com ./validate-policy.sh policy.hujson

set -e

TAILNET="${TS_TAILNET:--}"
TOKEN="${TS_API_KEY}"
POLICY_FILE="${1:-policy.hujson}"

if [[ -z "$TOKEN" ]]; then
  echo "ERROR: TS_API_KEY must be set"
  exit 1
fi

if [[ ! -f "$POLICY_FILE" ]]; then
  echo "ERROR: Policy file not found: $POLICY_FILE"
  exit 1
fi

echo "Validating: $POLICY_FILE"

RESULT=$(curl -s \
  -w "\n%{http_code}" \
  -u "${TOKEN}:" \
  -H "Content-Type: application/hujson" \
  --data-binary "@${POLICY_FILE}" \
  "https://api.tailscale.com/api/v2/tailnet/${TAILNET}/acl/validate")

HTTP_STATUS=$(echo "$RESULT" | tail -1)
BODY=$(echo "$RESULT" | sed '$d')

if [[ "$HTTP_STATUS" == "200" && "$BODY" == "{}" ]]; then
  echo "OK — policy is valid and all tests pass"
  exit 0
else
  echo "FAILED (HTTP $HTTP_STATUS):"
  echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
  exit 1
fi
```

### apply-policy.sh

```bash
#!/bin/bash
# Applies a policy file to Tailscale (validates first, then applies)
# Usage: TS_API_KEY=tskey-api-xxx TS_TAILNET=example.com ./apply-policy.sh policy.hujson

set -e

TAILNET="${TS_TAILNET:--}"
TOKEN="${TS_API_KEY}"
POLICY_FILE="${1:-policy.hujson}"

if [[ -z "$TOKEN" ]]; then
  echo "ERROR: TS_API_KEY must be set"
  exit 1
fi

# Step 1: Validate
echo "Validating policy..."
VALIDATE=$(curl -s \
  -u "${TOKEN}:" \
  -H "Content-Type: application/hujson" \
  --data-binary "@${POLICY_FILE}" \
  "https://api.tailscale.com/api/v2/tailnet/${TAILNET}/acl/validate")

if [[ "$VALIDATE" != "{}" ]]; then
  echo "Validation failed — aborting:"
  echo "$VALIDATE" | python3 -m json.tool 2>/dev/null || echo "$VALIDATE"
  exit 1
fi

echo "Validation passed. Fetching current ETag..."

# Step 2: Get ETag for safe apply
RESPONSE=$(curl -si \
  -u "${TOKEN}:" \
  -H "Accept: application/hujson" \
  "https://api.tailscale.com/api/v2/tailnet/${TAILNET}/acl")

ETAG=$(echo "$RESPONSE" | grep -i "^etag:" | awk '{print $2}' | tr -d '\r\n"')

echo "Applying policy (ETag: ${ETAG})..."

# Step 3: Apply with ETag collision detection
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST \
  -u "${TOKEN}:" \
  -H "Content-Type: application/hujson" \
  -H "If-Match: \"${ETAG}\"" \
  --data-binary "@${POLICY_FILE}" \
  "https://api.tailscale.com/api/v2/tailnet/${TAILNET}/acl")

case "$HTTP_STATUS" in
  200) echo "Applied successfully." ;;
  412) echo "ERROR: Policy was modified by someone else since you fetched it. Pull the latest and retry." ; exit 1 ;;
  *)   echo "ERROR: Unexpected HTTP status $HTTP_STATUS" ; exit 1 ;;
esac
```

### get-policy.sh

```bash
#!/bin/bash
# Fetches current policy and saves to file
# Usage: TS_API_KEY=tskey-api-xxx TS_TAILNET=example.com ./get-policy.sh > policy.hujson

set -e

TAILNET="${TS_TAILNET:--}"
TOKEN="${TS_API_KEY}"

curl -s \
  -u "${TOKEN}:" \
  -H "Accept: application/hujson" \
  "https://api.tailscale.com/api/v2/tailnet/${TAILNET}/acl"
```

---

## HTTP status codes

| Code | Meaning |
|---|---|
| 200 | Success |
| 400 | Bad request (malformed HuJSON, invalid policy syntax) |
| 401 | Authentication failed |
| 403 | Insufficient permissions |
| 412 | Precondition failed — ETag mismatch (concurrent edit) |
| 422 | Validation error (tests failed, semantic error in policy) |
| 429 | Rate limited |
| 500 | Server error |

---

## Working with the API in CI/CD outside GitHub Actions

If you're using GitLab CI, Bitbucket Pipelines, Jenkins, or another CI system, the core workflow is the same — just replace the GitHub Action with direct API calls:

```yaml
# GitLab CI example
validate-tailscale-policy:
  image: alpine
  script:
    - apk add curl jq
    - |
      RESULT=$(curl -s \
        -u "${TS_API_KEY}:" \
        -H "Content-Type: application/hujson" \
        --data-binary "@policy.hujson" \
        "https://api.tailscale.com/api/v2/tailnet/${TS_TAILNET}/acl/validate")
      if [[ "$RESULT" != "{}" ]]; then
        echo "Validation failed: $RESULT"
        exit 1
      fi
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'

apply-tailscale-policy:
  image: alpine
  script:
    - apk add curl jq
    - ./scripts/apply-policy.sh policy.hujson
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
```
