# Tailscale Policy File Reference

## Table of contents
1. [All source/destination values](#source-destination-values)
2. [Full acls syntax](#full-acls-syntax)
3. [Grants syntax (new)](#grants-syntax)
4. [SSH rules in detail](#ssh-rules-in-detail)
5. [nodeAttrs section](#nodeattrs-section)
6. [Tests and sshTests](#tests-and-sshtests)
7. [Complete small-team example](#complete-small-team-example)
8. [Complete enterprise example](#complete-enterprise-example)

---

## Source/destination values

| Value | Meaning |
|---|---|
| `*` | All tailnet traffic (src) / any destination (dst) |
| `user@domain.com` | Specific user |
| `group:name` | Custom group |
| `tag:name` | Tagged devices |
| `autogroup:member` | All tailnet members |
| `autogroup:self` | User's own devices |
| `autogroup:admin` | Tailnet admins |
| `autogroup:tagged` | Any tagged device |
| `autogroup:internet` | Internet via exit node (dst only) |
| `autogroup:shared` | Sharing invitation acceptors (src only) |
| `100.x.x.x` | Specific Tailscale IP |
| `192.168.0.0/24` | CIDR range |
| `hostname` | Alias defined in `hosts` section |

## Port syntax in dst

| Format | Meaning |
|---|---|
| `:*` | Any port |
| `:22` | Single port |
| `:80,443` | Multiple ports |
| `:1000-2000` | Port range |
| `:0` | Used for ICMP in tests |

## Protocol filter in acls

Add `"proto": "tcp"` or `"proto": "udp"` to an ACL rule to restrict by protocol. Omitting it means TCP + UDP.

---

## Full acls syntax

```hujson
"acls": [
  {
    "action": "accept",           // only valid value
    "src":    ["group:eng"],      // one or more sources
    "dst":    ["tag:web:443"],    // one or more dest:port
    "proto":  "tcp",              // optional: "tcp", "udp", "icmp"
  },
  // Allow all ports from devops to everything
  {
    "action": "accept",
    "src":    ["group:devops"],
    "dst":    ["*:*"],
  },
  // Multiple destinations in one rule
  {
    "action": "accept",
    "src":    ["tag:monitoring"],
    "dst":    ["tag:prod:9100", "tag:staging:9100"],
  },
],
```

---

## Grants syntax

Grants are the recommended replacement for acls in new policies. Key differences:
- No `action` field (always grant)
- Port/protocol moves from `dst` to `ip` field
- Supports application-layer capability grants

```hujson
"grants": [
  // Basic network grant
  {
    "src": ["group:eng"],
    "dst": ["tag:web"],
    "ip":  ["tcp:443", "tcp:80"],
  },
  // All protocols/ports
  {
    "src": ["group:devops"],
    "dst": ["*"],
    "ip":  ["*"],
  },
  // With device posture requirement
  {
    "src":        ["group:sre"],
    "srcPosture": ["posture:corp-device"],
    "dst":        ["tag:prod"],
    "ip":         ["*"],
  },
  // Kubernetes operator capability grant
  {
    "src": ["group:k8s-admins"],
    "dst": ["tag:k8s-operator"],
    "app": {
      "tailscale.com/cap/kubernetes": [
        {
          "impersonate": {
            "groups": ["system:masters"],
          },
        },
      ],
    },
  },
],
```

### Converting acls to grants

```hujson
// BEFORE (ACL):
{
  "action": "accept",
  "proto":  "tcp",
  "src":    ["group:eng"],
  "dst":    ["tag:web:80", "tag:web:443"],
}

// AFTER (Grant):
{
  "src": ["group:eng"],
  "dst": ["tag:web"],
  "ip":  ["tcp:80", "tcp:443"],
}
```

---

## SSH rules in detail

```hujson
"ssh": [
  // Basic accept: engineers SSH to dev as any non-root user
  {
    "action": "accept",
    "src":    ["group:engineering"],
    "dst":    ["tag:dev"],
    "users":  ["autogroup:nonroot"],
  },
  // check: re-authenticate every 8 hours
  {
    "action":      "check",
    "checkPeriod": "8h",
    "src":         ["group:devops"],
    "dst":         ["tag:prod"],
    "users":       ["root", "ubuntu"],
  },
  // Users always SSH to their own devices
  {
    "action": "accept",
    "src":    ["autogroup:member"],
    "dst":    ["autogroup:self"],
    "users":  ["autogroup:nonroot"],
  },
  // Pass specific env vars through SSH sessions
  {
    "action":    "accept",
    "src":       ["group:devops"],
    "dst":       ["tag:prod"],
    "users":     ["ubuntu"],
    "acceptEnv": ["EDITOR", "GIT_*", "TERM"],
  },
],
```

SSH `users` values:
- `autogroup:nonroot` — any non-root user
- `localpart:*@domain.com` — username matched from email (e.g. alice@example.com → alice)
- Explicit username strings like `ubuntu`, `root`, `ec2-user`

---

## nodeAttrs section

Apply additional attributes to specific devices:

```hujson
"nodeAttrs": [
  // Enable Tailscale Funnel for web servers
  {
    "target": ["tag:web"],
    "attr":   ["funnel"],
  },
  // Enable NextDNS for all devices
  {
    "target": ["*"],
    "attr":   ["nextdns:abc123"],
  },
  // App connector configuration
  {
    "target": ["tag:app-connector"],
    "app": {
      "tailscale.com/app-connectors": [
        {
          "name":       "internal-saas",
          "connectors": ["tag:app-connector"],
          "domains":    ["tool.internal.example.com"],
        },
      ],
    },
  },
],
```

---

## Tests and sshTests

### Network tests (tests)

```hujson
"tests": [
  {
    "src":    "alice@example.com",
    "accept": ["tag:dev:22"],         // must be allowed
    "deny":   ["tag:prod:22"],        // must be denied
  },
  // Test with protocol
  {
    "src":   "tag:monitoring",
    "proto": "icmp",
    "accept": ["tag:prod:0"],         // port 0 for ICMP
  },
  // Test with device posture context
  {
    "src": "alice@example.com",
    "srcPostureAttrs": {
      "node:os": "macos",
    },
    "accept": ["tag:dev:22"],
  },
],
```

Note: destinations in tests cannot use CIDR notation — use host aliases from `hosts`.

### SSH tests (sshTests)

```hujson
"sshTests": [
  {
    "src":    "alice@example.com",
    "dst":    ["tag:dev"],
    "accept": ["alice", "autogroup:nonroot"],
    "deny":   ["root"],
  },
  {
    "src":   "carl@example.com",
    "dst":   ["tag:prod"],
    "check": ["root", "ubuntu"],    // allowed but requires check
  },
],
```

---

## Complete small-team example

```hujson
// Small startup policy
// Managed via git: https://github.com/example/tailscale-policy
{
  "groups": {
    "group:eng": ["alice@startup.com", "bob@startup.com"],
    "group:ops": ["carl@startup.com"],
  },

  "hosts": {
    "prod-db":   "100.64.1.10",
    "staging":   "100.64.1.20",
  },

  "tagOwners": {
    "tag:prod":    ["autogroup:admin"],
    "tag:staging": ["group:ops"],
    "tag:dev":     ["group:ops", "group:eng"],
    "tag:ci":      ["group:ops", "tag:ci"],
  },

  "acls": [
    // Engineers: dev + staging read access
    {"action": "accept", "src": ["group:eng"],  "dst": ["tag:dev:*"]},
    {"action": "accept", "src": ["group:eng"],  "dst": ["tag:staging:80,443"]},
    // Ops: full access
    {"action": "accept", "src": ["group:ops"],  "dst": ["*:*"]},
    // CI deploys to staging
    {"action": "accept", "src": ["tag:ci"],     "dst": ["tag:staging:443"]},
    // Everyone accesses their own devices
    {"action": "accept", "src": ["autogroup:member"], "dst": ["autogroup:self:*"]},
  ],

  "ssh": [
    {"action": "check", "checkPeriod": "8h", "src": ["group:ops"], "dst": ["tag:prod"],    "users": ["ubuntu"]},
    {"action": "accept",                     "src": ["group:ops"], "dst": ["tag:staging"], "users": ["ubuntu"]},
    {"action": "accept", "src": ["autogroup:member"], "dst": ["autogroup:self"], "users": ["autogroup:nonroot"]},
  ],

  "tests": [
    {"src": "alice@startup.com", "accept": ["tag:dev:22", "tag:staging:443"], "deny": ["tag:prod:22"]},
    {"src": "carl@startup.com",  "accept": ["tag:prod:22", "tag:prod:443"]},
    {"src": "tag:ci",            "accept": ["tag:staging:443"],               "deny": ["tag:prod:443"]},
  ],
}
```

---

## Complete enterprise example

```hujson
// Enterprise policy with device posture
{
  "groups": {
    "group:engineers": ["alice@corp.com", "bob@corp.com"],
    "group:sre":       ["carl@corp.com"],
    "group:security":  ["diana@corp.com"],
  },

  "tagOwners": {
    "tag:prod":        ["group:sre"],
    "tag:staging":     ["group:sre", "group:engineers"],
    "tag:exit-node":   ["autogroup:admin"],
    "tag:vpc-router":  ["autogroup:admin"],
    "tag:monitoring":  ["group:sre"],
  },

  "postures": {
    "posture:corp-device": [
      "node:tsReleaseTrack == 'stable'",
      "node:tsVersion >= '1.60'",
    ],
  },

  "grants": [
    // SRE with compliant device gets prod access
    {
      "src":        ["group:sre"],
      "srcPosture": ["posture:corp-device"],
      "dst":        ["tag:prod"],
      "ip":         ["*"],
    },
    // Everyone gets staging
    {
      "src": ["group:engineers", "group:sre"],
      "dst": ["tag:staging"],
      "ip":  ["*"],
    },
    // Monitoring reads metrics from all environments
    {
      "src": ["tag:monitoring"],
      "dst": ["tag:prod", "tag:staging"],
      "ip":  ["tcp:9100", "tcp:9090"],
    },
    // Own devices always
    {
      "src": ["autogroup:member"],
      "dst": ["autogroup:self"],
      "ip":  ["*"],
    },
  ],

  "autoApprovers": {
    "exitNode": ["tag:exit-node"],
    "routes": {
      "10.0.0.0/8":   ["tag:vpc-router"],
    },
  },

  "tests": [
    {"src": "alice@corp.com", "accept": ["tag:staging:443"], "deny": ["tag:prod:443"]},
    {"src": "carl@corp.com",  "accept": ["tag:prod:22",  "tag:staging:443"]},
  ],
}
```
