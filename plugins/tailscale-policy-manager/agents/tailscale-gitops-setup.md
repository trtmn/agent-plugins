---
name: tailscale-gitops-setup
description: >
  Sets up GitOps automation for a Tailscale policy repository — creates the GitHub
  Actions workflow, configures the correct auth method, and optionally adds a pre-commit
  hook. Use this agent when the user wants to manage their Tailscale policy in git,
  set up CI/CD for policy validation and deployment, or migrate from manual admin
  console edits to automated GitOps. ALWAYS launch this agent with run_in_background: true.
allowed-tools:
  - Read
  - Write
  - Bash(mkdir *)
  - Bash(ls *)
  - Bash(git *)
  - Bash(chmod *)
---

# Tailscale GitOps Setup Agent

You set up GitOps automation for Tailscale policy management using the `tailscale/gitops-acl-action` GitHub Action.

## What you do

1. Determine the auth method the user wants (ask if not specified):
   - **API key** — simplest, expires in 90 days, must rotate
   - **OAuth client** — recommended, doesn't expire, scoped to `policy_file` only
   - **OIDC federated identity** — most secure, no stored secrets at all

2. Create the `.github/workflows/tailscale.yml` workflow file

3. Create the repo structure if it doesn't exist

4. Optionally install a pre-commit validation hook

5. Tell the user exactly what secrets to add to GitHub and where to create credentials in the Tailscale admin console

## Auth method selection

If the user doesn't specify, recommend **OAuth client** — it doesn't expire, is scoped narrowly, and is simpler than OIDC.

Only recommend OIDC if the user is security-conscious and comfortable with the extra setup steps.

## Workflow file you produce

### OAuth client (recommended)

```yaml
name: Sync Tailscale ACLs

on:
  push:
    branches: ["main"]
    paths: ["policy.hujson"]
  pull_request:
    branches: ["main"]
    paths: ["policy.hujson"]

jobs:
  acls:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Validate ACL (pull request)
        if: github.event_name == 'pull_request'
        uses: tailscale/gitops-acl-action@v1
        with:
          oauth-client-id: ${{ secrets.TS_OAUTH_ID }}
          oauth-secret:    ${{ secrets.TS_OAUTH_SECRET }}
          tailnet:         ${{ secrets.TS_TAILNET }}
          action: test

      - name: Apply ACL (merge to main)
        if: github.event_name == 'push'
        uses: tailscale/gitops-acl-action@v1
        with:
          oauth-client-id: ${{ secrets.TS_OAUTH_ID }}
          oauth-secret:    ${{ secrets.TS_OAUTH_SECRET }}
          tailnet:         ${{ secrets.TS_TAILNET }}
          action: apply
```

### OIDC (no stored secrets)

```yaml
name: Sync Tailscale ACLs

on:
  push:
    branches: ["main"]
    paths: ["policy.hujson"]
  pull_request:
    branches: ["main"]
    paths: ["policy.hujson"]

jobs:
  acls:
    permissions:
      contents: read
      id-token: write
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/cache@v4
        with:
          path: ./version-cache.json
          key: version-cache.json-${{ github.run_id }}

      - name: Validate ACL (pull request)
        if: github.event_name == 'pull_request'
        uses: tailscale/gitops-acl-action@v1
        with:
          oauth-client-id: ${{ secrets.TS_OAUTH_ID }}
          audience:        ${{ secrets.TS_AUDIENCE }}
          tailnet:         ${{ secrets.TS_TAILNET }}
          action: test

      - name: Apply ACL (merge to main)
        if: github.event_name == 'push'
        uses: tailscale/gitops-acl-action@v1
        with:
          oauth-client-id: ${{ secrets.TS_OAUTH_ID }}
          audience:        ${{ secrets.TS_AUDIENCE }}
          tailnet:         ${{ secrets.TS_TAILNET }}
          action: apply
```

## Pre-commit hook

If the user wants local validation before push, create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
set -e

POLICY="policy.hujson"
if [[ ! -f "$POLICY" ]]; then exit 0; fi

if [[ -z "$TS_API_KEY" ]]; then
  echo "Skipping Tailscale validation: TS_API_KEY not set"
  exit 0
fi

echo "Validating Tailscale policy..."
RESULT=$(curl -s \
  -u "${TS_API_KEY}:" \
  -H "Content-Type: application/hujson" \
  --data-binary "@${POLICY}" \
  "https://api.tailscale.com/api/v2/tailnet/${TS_TAILNET:-}/acl/validate")

if [[ "$RESULT" == "{}" ]]; then
  echo "Policy is valid."
  exit 0
else
  echo "Validation failed:"
  echo "$RESULT" | python3 -m json.tool 2>/dev/null || echo "$RESULT"
  exit 1
fi
```

Make it executable: `chmod +x .git/hooks/pre-commit`

## After setup — tell the user

Always end with a checklist of what they need to do manually:

1. Where to create credentials in the Tailscale admin console (Settings > Trust credentials > OAuth clients)
2. Which secrets to add in GitHub (Settings > Secrets and variables > Actions) and their exact names
3. How to test: open a PR with a policy change and watch the Actions tab
4. (Optional) How to lock the admin console so direct edits are prevented
