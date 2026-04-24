---
name: tailscale-policy-manager
description: >
  Expert guide for managing Tailscale tailnet policy files. Covers the HuJSON policy
  file format, all policy sections (grants, acls, groups, tags, postures, SSH rules,
  autoApprovers, nodeAttrs, tests), the Tailscale API for validating and applying
  policies, and GitOps automation via GitHub Actions. Grants are now GA and the default
  for new tailnets; acls are supported indefinitely but won't receive new features.
  Use this skill whenever the user is working with Tailscale ACLs or policy files,
  wants to set up git-based policy management, needs to write or debug access rules,
  wants to automate policy deployment, or mentions tailnet, Tailscale ACL, policy.hujson,
  gitops-acl-action, grants, postures, or Tailscale network permissions. Also trigger
  for questions like "how do I restrict which devices can talk to each other on
  Tailscale", "how do I set up Tailscale SSH rules", or "how do I require device
  posture checks for prod access."
---

# Tailscale Policy Manager

Tailscale controls who can talk to what on your private network through a single **policy file** — a HuJSON document you manage in the admin console or, better yet, in a git repository with automated deployment.

## Quick orientation

When a user asks about Tailscale policy/ACL work, figure out what they need:

- **Writing or editing rules** → delegate to the `tailscale-policy-writer` agent (background)
- **Reviewing a policy for security issues** → delegate to the `tailscale-policy-reviewer` agent (background)
- **Setting up GitOps / GitHub Actions** → delegate to the `tailscale-gitops-setup` agent (background)
- **Using the API directly / scripting** → `references/api-reference.md`; bundled scripts in `scripts/` (`validate-policy.sh`, `apply-policy.sh`, `get-policy.sh`)
- **Debugging why something isn't allowed** → check the `tests` block section below and the ACL rule syntax
- **Full policy file schema** → `references/policy-file-reference.md`

## Grants vs ACLs (as of 2025)

**Grants are GA and the default for new tailnets.** For new policies, always use `grants`. For existing policies using `acls`, continue using `acls` unless the user asks to migrate — both syntaxes are supported indefinitely and can coexist in the same file.

Key difference: only `grants` will receive new features (posture checks, app-layer capabilities). `acls` are network-layer only.

## The HuJSON format

Tailscale policy files use **HuJSON** — standard JSON plus two things:
- Line comments (`//`) and block comments (`/* */`)
- Trailing commas on the last item in any array or object

This matters because it means you can document your rules inline, which is valuable for a security-sensitive file that multiple people edit.

```hujson
{
  // Engineers can reach dev servers on any port
  "acls": [
    {
      "action": "accept",
      "src":    ["group:engineering"],
      "dst":    ["tag:dev:*"],  // trailing comma is fine
    },
  ],
}
```

## Core policy file sections

The policy file is deny-by-default. You're always writing rules that explicitly grant access.

### groups
Named sets of users. Group names must start with `group:`.

```hujson
"groups": {
  "group:engineering": ["alice@example.com", "bob@example.com"],
  "group:devops":      ["carl@example.com"],
},
```

Groups can't contain other groups. Use email addresses as members.

### tagOwners
Tags are labels applied to devices (not users). Tag owners control who can tag devices with that label.

```hujson
"tagOwners": {
  "tag:prod":    ["autogroup:admin"],    // only admins can tag prod
  "tag:dev":     ["group:engineering"],  // engineers can tag dev machines
  "tag:ci":      ["tag:ci"],             // CI devices can self-tag
},
```

An empty array `[]` means only admins can use the tag.

### acls
The main access control rules. Each rule grants access — there's no "deny" action because everything not explicitly allowed is denied.

```hujson
"acls": [
  {
    "action": "accept",
    "src":    ["group:engineering"],
    "dst":    ["tag:dev:22,443"],   // SSH and HTTPS to dev-tagged devices
  },
  {
    "action": "accept",
    "proto":  "tcp",                // optional protocol filter
    "src":    ["tag:monitoring"],
    "dst":    ["tag:prod:9100"],    // Prometheus port on prod
  },
],
```

Common source/destination values:
- `*` — everyone/everything
- `user@domain.com` — specific user
- `group:name` — named group
- `tag:name` — tagged devices
- `autogroup:member` — all tailnet members
- `autogroup:self` — user's own devices
- `autogroup:admin` — tailnet admins
- `100.x.x.x` — specific Tailscale IP
- Hostname defined in `hosts` section

Port syntax in `dst`: `:22` (single), `:80,443` (multiple), `:1000-2000` (range), `:*` (all)

### hosts (aliases)
Named shortcuts for IPs and CIDRs:

```hujson
"hosts": {
  "prod-db":     "100.64.0.10",
  "aws-vpc":     "10.0.0.0/8",
},
```

Then use `prod-db:5432` in ACL rules instead of the raw IP.

### ssh
Tailscale SSH rules (requires Tailscale SSH to be enabled on the device):

```hujson
"ssh": [
  {
    "action": "accept",
    "src":    ["group:engineering"],
    "dst":    ["tag:dev"],
    "users":  ["ubuntu", "autogroup:nonroot"],
  },
  {
    "action":      "check",      // allow but re-authenticate periodically
    "checkPeriod": "8h",
    "src":         ["group:devops"],
    "dst":         ["tag:prod"],
    "users":       ["root", "ubuntu"],
  },
],
```

`action: "check"` prompts for re-auth after `checkPeriod`. Use this for sensitive servers.

### autoApprovers
Without this, admins must manually approve every subnet route advertisement. With it, matching devices are approved automatically:

```hujson
"autoApprovers": {
  "routes": {
    "10.0.0.0/8":   ["tag:vpc-router"],
    "192.168.0.0/16": ["group:network-team"],
  },
  "exitNode": ["tag:exit-node"],
},
```

### tests
**Always include tests.** They run every time the policy is saved and prevent accidental regressions:

```hujson
"tests": [
  {
    "src":    "alice@example.com",
    "accept": ["tag:dev:22", "tag:staging:443"],
    "deny":   ["tag:prod:22"],          // verify prod is still locked down
  },
  {
    "src":    "tag:ci",
    "accept": ["tag:staging:443"],
    "deny":   ["tag:prod:443"],
  },
],
```

Tests fail loudly if you accidentally grant too much or too little access — they're your safety net.

## ACLs vs Grants

Tailscale is migrating from `acls` to a newer `grants` syntax. For new policies, consider `grants` — it separates the destination host from the port/protocol:

```hujson
// ACL style (still works, supported forever)
"acls": [
  {"action": "accept", "src": ["group:eng"], "dst": ["tag:web:80,443"]},
]

// Grants style (recommended for new rules)
"grants": [
  {"src": ["group:eng"], "dst": ["tag:web"], "ip": ["tcp:80", "tcp:443"]},
]
```

You **can** mix `acls` and `grants` in the same file — Tailscale explicitly supports this and recommends it as an incremental migration path. Use `grants` for new rules while keeping existing `acls`; both are evaluated together. Only `grants` will receive new features going forward (like app-layer capabilities and posture checks), but `acls` are supported indefinitely.

## Practical design guidance

**Use tags for machines, groups for humans.** Tag-based rules survive personnel changes; user-based rules become stale.

**Least privilege by default.** Don't open `:*` unless you have a good reason. Be explicit about which ports each service needs.

**Document with comments.** Policy files are security-critical and reviewed by multiple people. Use comments to explain the intent of non-obvious rules.

**Test your denials, not just your allows.** The most important tests are the ones that verify locked-down resources stay locked down.

## Reference files

For detailed information, read these as needed:

- **`references/policy-file-reference.md`** — Complete field reference, all autogroup values, protocol syntax, grants details, real-world example policies
- **`references/gitops-setup.md`** — Step-by-step GitHub Actions setup, all three auth methods (API key, OAuth, OIDC federated), multi-tailnet patterns, pre-commit hooks
- **`references/api-reference.md`** — Tailscale API endpoints, authentication, ETag-based safe updates, shell scripts for validation and deployment
