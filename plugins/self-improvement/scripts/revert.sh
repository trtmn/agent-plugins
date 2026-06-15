#!/usr/bin/env bash
# Undo a promotion the self-improvement pipeline made.
#   revert.sh <PROMO-hex>   → remove the promoted block from its target CLAUDE.md and
#                             append a [REVERT-<hex>] entry to ~/.learnings/CHANGELOG.md.
#   revert.sh               → list recent PROMO ids.
#
# Relies on the PROMO entry storing the exact promoted text in a fenced ```text block
# (the self-improvement agent writes it that way). If the text can no longer be found
# verbatim in the target (hand-edited since), it changes nothing and reports.
set -uo pipefail

CHANGELOG="$HOME/.learnings/CHANGELOG.md"

if [[ ! -f "$CHANGELOG" ]]; then
  echo "No changelog at $CHANGELOG — nothing to revert." >&2
  exit 1
fi

ARG="${1:-}"

if [[ -z "$ARG" ]]; then
  echo "Recent promotions (pass one of these ids to revert):"
  grep -E '^## \[PROMO-' "$CHANGELOG" | tail -n 20 || echo "  (none found)"
  exit 0
fi

# Normalize: accept "a3f7c1" or "PROMO-a3f7c1".
HEX="${ARG#PROMO-}"

CHANGELOG="$CHANGELOG" PROMO_HEX="$HEX" python3 <<'PY'
import os, re, sys, datetime

changelog = os.environ["CHANGELOG"]
hex_id = os.environ["PROMO_HEX"]
text = open(changelog, encoding="utf-8").read()

# Isolate the [PROMO-<hex>] block: from its heading to the next "## [" or EOF.
m = re.search(r'^## \[PROMO-' + re.escape(hex_id) + r'\].*?(?=^## \[|\Z)',
              text, flags=re.S | re.M)
if not m:
    print(f"PROMO-{hex_id} not found in {changelog}.", file=sys.stderr)
    sys.exit(2)
block = m.group(0)

def field(name):
    fm = re.search(r'^- \*\*' + re.escape(name) + r'\*\*:\s*(.*)$', block, flags=re.M)
    return fm.group(1).strip() if fm else ""

target_raw = field("Target")
section = field("Section")
# Target may read like "~/.claude/CLAUDE.md (or project ...)" — take the leading path.
target = target_raw.split(" (")[0].strip()
target = os.path.expanduser(target)

# Extract the exact promoted text from the fenced block after "- **Promoted text**:".
# Tolerant of an optionally-indented fence; the captured text is treated as verbatim.
pm = re.search(r'- \*\*Promoted text\*\*:[^\n]*\n[ \t]*```[^\n]*\n(.*?)\n[ \t]*```',
               block, flags=re.S)
if not pm:
    print(f"PROMO-{hex_id} has no fenced 'Promoted text' block — cannot auto-revert. "
          f"Remove it from {target!r} (section {section!r}) by hand, then add a REVERT note.",
          file=sys.stderr)
    sys.exit(3)
promoted = pm.group(1)

if not target or not os.path.isfile(target):
    print(f"Target file {target!r} not found — cannot auto-revert.", file=sys.stderr)
    sys.exit(4)

content = open(target, encoding="utf-8").read()
if promoted not in content:
    print(f"Promoted text for PROMO-{hex_id} no longer present verbatim in {target!r} "
          f"(it was edited since). No change made — remove it manually if needed.",
          file=sys.stderr)
    sys.exit(5)

# Remove the promoted text plus one adjacent blank line to avoid leaving a gap.
new = content.replace("\n\n" + promoted, "", 1)
if new == content:
    new = content.replace(promoted + "\n", "", 1)
if new == content:
    new = content.replace(promoted, "", 1)
open(target, "w", encoding="utf-8").write(new)

# Append a REVERT entry (append-only changelog; never edit the original PROMO).
ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
rev_hex = os.urandom(3).hex()
entry = (
    f"\n## [REVERT-{rev_hex}] Reverted PROMO-{hex_id}\n"
    f"- **Timestamp**: {ts}\n"
    f"- **Source**: PROMO-{hex_id}\n"
    f"- **Disposition**: reverted\n"
    f"- **Reason**: Manual revert via /self-improvement:revert\n"
    f"- **Removed from**: {target} / {section}\n"
)
with open(changelog, "a", encoding="utf-8") as f:
    f.write(entry)

print(f"Reverted PROMO-{hex_id}: removed the promoted block from {target} "
      f"(section {section!r}) and logged REVERT-{rev_hex}.")
PY
