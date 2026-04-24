# Tailscale GitOps Setup Guide

Managing your Tailscale policy file in git gives you: version history, PR-based review, automatic validation on every change, and no risk of someone fat-fingering a rule in the admin console.

## Table of contents
1. [Repository structure](#repository-structure)
2. [Auth option A: API key](#auth-option-a-api-key-simplest)
3. [Auth option B: OAuth client (recommended)](#auth-option-b-oauth-client-recommended)
4. [Auth option C: OIDC federated identity (best practice)](#auth-option-c-oidc-federated-identity-best-practice)
5. [Multi-tailnet setup](#multi-tailnet-setup)
6. [Local pre-commit validation](#local-pre-commit-validation)
7. [Admin console lockdown](#admin-console-lockdown)

---

## Repository structure

```
tailscale-policy/
├── policy.hujson               # your policy file
└── .github/
    └── workflows/
        └── tailscale.yml       # the CI/CD workflow
```

For multiple tailnets:
```
tailscale-policy/
├── tailnets/
│   ├── prod.hujson
│   └── staging.hujson
└── .github/
    └── workflows/
        └── tailscale.yml
```

The official GitHub Action is `tailscale/gitops-acl-action`. It does two things:
- `action: test` — validates the policy and runs tests, without applying
- `action: apply` — validates, then pushes to your tailnet

The standard pattern: test on PRs, apply on merge to main.

---

## Auth option A: API key (simplest)

Create an API key in the Tailscale admin console under **Settings > Keys > Generate API key**. Set expiry to 90 days (maximum).

**Secrets to add to your GitHub repo** (Settings > Secrets and variables > Actions):
- `TS_API_KEY` — your API key
- `TS_TAILNET` — your tailnet name (e.g. `example.com` or the `-` alias for your default tailnet)

```yaml
# .github/workflows/tailscale.yml
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
          api-key: ${{ secrets.TS_API_KEY }}
          tailnet:  ${{ secrets.TS_TAILNET }}
          action:   test

      - name: Apply ACL (merge to main)
        if: github.event_name == 'push'
        uses: tailscale/gitops-acl-action@v1
        with:
          api-key: ${{ secrets.TS_API_KEY }}
          tailnet:  ${{ secrets.TS_TAILNET }}
          action:   apply
```

Downside: API keys expire, you'll need to rotate them.

---

## Auth option B: OAuth client (recommended)

OAuth clients don't expire and can be scoped to only the `policy_file` permission (not full admin).

**Create an OAuth client:**
1. Go to **Settings > Trust credentials > OAuth clients**
2. Create a new client with scope `policy_file` (read + write)
3. Save the client ID and secret

**Secrets to add:**
- `TS_OAUTH_ID` — OAuth client ID
- `TS_OAUTH_SECRET` — OAuth client secret
- `TS_TAILNET` — tailnet name

```yaml
# .github/workflows/tailscale.yml
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

---

## Auth option C: OIDC federated identity (best practice)

No stored secrets at all — GitHub's OIDC provider issues short-lived tokens bound to your specific repo. This is the most secure approach.

**Setup in Tailscale admin console:**
1. Go to **Settings > Trust credentials > OAuth clients**
2. Create an OAuth client with `policy_file` scope
3. Under "Federated identity", add your GitHub repo as a trusted issuer
4. Set the audience value (you'll use this in the workflow)

**Secrets to add:**
- `TS_OAUTH_ID` — OAuth client ID
- `TS_AUDIENCE` — audience string configured in the OAuth client
- `TS_TAILNET` — tailnet name

```yaml
# .github/workflows/tailscale.yml
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
      contents:  read
      id-token:  write   # required to request OIDC tokens

    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Optional: cache version file to avoid redundant API calls
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

---

## Multi-tailnet setup

When you manage multiple tailnets (e.g. prod and staging), use separate jobs with separate credentials:

```yaml
# .github/workflows/tailscale.yml
name: Sync Tailscale ACLs

on:
  push:
    branches: ["main"]
  pull_request:
    branches: ["main"]

jobs:
  sync-prod:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: tailscale/gitops-acl-action@v1
        with:
          oauth-client-id: ${{ secrets.PROD_TS_OAUTH_ID }}
          oauth-secret:    ${{ secrets.PROD_TS_OAUTH_SECRET }}
          tailnet:         ${{ secrets.PROD_TS_TAILNET }}
          policy-file:     ./tailnets/prod.hujson
          action: ${{ github.event_name == 'push' && 'apply' || 'test' }}

  sync-staging:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: tailscale/gitops-acl-action@v1
        with:
          oauth-client-id: ${{ secrets.STAGING_TS_OAUTH_ID }}
          oauth-secret:    ${{ secrets.STAGING_TS_OAUTH_SECRET }}
          tailnet:         ${{ secrets.STAGING_TS_TAILNET }}
          policy-file:     ./tailnets/staging.hujson
          action: ${{ github.event_name == 'push' && 'apply' || 'test' }}
```

Tip: apply changes to staging automatically, but require a manual approval step for prod. You can do this with GitHub Environments and protection rules.

---

## Local pre-commit validation

Validate before you even push by adding a pre-commit hook. This catches syntax errors and failed test assertions locally.

### Simple git hook

```bash
# .git/hooks/pre-commit
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
  "https://api.tailscale.com/api/v2/tailnet/${TS_TAILNET}/acl/validate")

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

### Using lefthook (for teams)

Install `lefthook` and commit a config so the whole team gets the hook:

```yaml
# lefthook.yml
pre-commit:
  commands:
    tailscale-policy:
      glob: "*.hujson"
      run: |
        RESULT=$(curl -s \
          -u "${TS_API_KEY}:" \
          -H "Content-Type: application/hujson" \
          --data-binary "@{staged_files}" \
          "https://api.tailscale.com/api/v2/tailnet/${TS_TAILNET}/acl/validate")
        if [[ "$RESULT" != "{}" ]]; then
          echo "Tailscale policy validation failed: $RESULT"
          exit 1
        fi
```

### HuJSON syntax check (no network needed)

For pure syntax checking without hitting the API:

```bash
# Install (requires Go)
go install github.com/tailscale/hujson/cmd/hujsonfmt@latest

# Check syntax
hujsonfmt policy.hujson

# Format in-place
hujsonfmt -w policy.hujson
```

This catches JSON syntax errors and HuJSON formatting issues but doesn't validate ACL logic or run tests.

---

## Admin console lockdown

Once you're managing policy via git, prevent accidental direct edits in the admin console:

1. Go to **Access controls** in the admin console
2. Find **Policy file management**
3. Enable "Prevent edits in the admin console"
4. Set the repository URL so teammates know where to make changes

Add this comment at the top of your policy file to make it clear to anyone who opens the admin console:

```hujson
// This tailnet's policy is managed via GitOps.
// Repository: https://github.com/your-org/tailscale-policy
// To make changes: open a PR against the main branch.
// Direct edits in this console are disabled.
{
  ...
}
```
