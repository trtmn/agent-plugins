#!/usr/bin/env bash
# xp.sh — side-quest XP ledger. Standalone; JSON to stdout, status to stderr.
#
# Usage:
#   xp.sh award <cr> <success|partial|wipe> <quest name...>
#   xp.sh status
#   xp.sh statusline
#
# Ledger lives at ~/.claude/side-quest/xp.json so every Claude agent/session
# (and a status bar command) can reach it.
set -euo pipefail

cmd="${1:-status}"
shift || true

exec python3 - "$cmd" "$@" <<'PY'
import json, os, sys, tempfile
from datetime import datetime, timezone
from pathlib import Path

LEDGER = Path.home() / ".claude" / "side-quest" / "xp.json"
HISTORY_CAP = 100

# D&D 5e XP by Challenge Rating (clamped to CR 10 for truly legendary quests)
XP_BY_CR = {1: 200, 2: 450, 3: 700, 4: 1100, 5: 1800,
            6: 2300, 7: 2900, 8: 3900, 9: 5000, 10: 5900}

# Pokemon Go-style geometric curve: L2=1000 XP, each step ×1.05, no level cap.
def _build_thresholds(target):
    """Build enough thresholds to cover target XP."""
    thresholds = [0, 1000]
    step = 1000
    while thresholds[-1] <= target:
        step = round(step * 1.05 / 50) * 50
        thresholds.append(thresholds[-1] + step)
    return thresholds


def level_for(xp):
    thresholds = _build_thresholds(xp)
    level = 1
    for i, threshold in enumerate(thresholds):
        if xp >= threshold:
            level = i + 1
    return level


def next_level_at(xp):
    thresholds = _build_thresholds(xp)
    for threshold in thresholds:
        if xp < threshold:
            return threshold
    return None  # shouldn't happen since we build past xp


def load():
    if LEDGER.exists():
        return json.loads(LEDGER.read_text())
    return {"total_xp": 0, "level": 1, "quests_completed": 0, "history": []}


def save(data):
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=LEDGER.parent, suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    os.replace(tmp, LEDGER)


cmd = sys.argv[1]
data = load()

if cmd == "award":
    if len(sys.argv) < 4:
        print("usage: xp.sh award <cr> <success|partial|wipe> <quest name...>", file=sys.stderr)
        sys.exit(2)
    cr = max(1, min(10, int(sys.argv[2])))
    outcome = sys.argv[3]
    if outcome not in ("success", "partial", "wipe"):
        print(f"unknown outcome: {outcome}", file=sys.stderr)
        sys.exit(2)
    rest = sys.argv[4:]
    source = "ambient"
    if len(rest) >= 2 and rest[0] == "--source":
        source = rest[1]
        rest = rest[2:]
    quest = " ".join(rest) or "Unnamed quest"

    base = XP_BY_CR[cr]
    awarded = {"success": base, "partial": base // 2, "wipe": 0}[outcome]

    old_level = level_for(data["total_xp"])
    data["total_xp"] += awarded
    if outcome != "wipe":
        data["quests_completed"] += 1
    data["level"] = level_for(data["total_xp"])
    data["history"].append({
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "quest": quest, "cr": cr, "outcome": outcome, "xp": awarded,
        "source": source,
        "leveled_up": data["level"] > old_level,
        "new_level": data["level"],
    })
    data["history"] = data["history"][-HISTORY_CAP:]
    nla = next_level_at(data["total_xp"])
    data["next_level_at"] = nla
    save(data)

    print(json.dumps({
        "awarded": awarded,
        "total_xp": data["total_xp"],
        "level": data["level"],
        "leveled_up": data["level"] > old_level,
        "quests_completed": data["quests_completed"],
        "next_level_at": nla,
    }))

elif cmd == "status":
    # Recompute level and next_level_at in case LEVEL_XP table changed since last award
    data["level"] = level_for(data["total_xp"])
    data["next_level_at"] = next_level_at(data["total_xp"])
    save(data)
    print(json.dumps({
        "total_xp": data["total_xp"],
        "level": data["level"],
        "quests_completed": data["quests_completed"],
        "next_level_at": data["next_level_at"],
    }))

elif cmd == "statusline":
    print(f"⚔️ Lv {data['level']} · {data['total_xp']:,} XP")

else:
    print(f"unknown command: {cmd}", file=sys.stderr)
    sys.exit(2)
PY
