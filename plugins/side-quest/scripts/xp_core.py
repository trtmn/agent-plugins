"""Core XP ledger logic for the side-quest plugin.

Pure/testable functions live here; xp.sh's CLI dispatch is a thin wrapper
around this module so the ledger math, event dedup, and tick batching can
be unit tested without shelling out or touching real files.
"""

import json
import os
import random
import subprocess
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

APPLIED_EVENT_IDS_CAP = 500
DEFAULT_TICK_XP = 10

# D&D 5e XP by Challenge Rating (clamped to CR 10 for truly legendary quests)
XP_BY_CR = {
    1: 200,
    2: 450,
    3: 700,
    4: 1100,
    5: 1800,
    6: 2300,
    7: 2900,
    8: 3900,
    9: 5000,
    10: 5900,
}


def _now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# Pokemon Go-style geometric curve: L2=1000 XP, each step x1.05, no level cap.
def _build_thresholds(target):
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


def new_award_event(machine, cr, outcome, quest, source="ambient"):
    base = XP_BY_CR[max(1, min(10, cr))]
    xp = {"success": base, "partial": base // 2, "wipe": 0}[outcome]
    return {
        "event_id": str(uuid.uuid4()),
        "machine": machine,
        "ts": _now_iso(),
        "kind": "award",
        "cr": cr,
        "outcome": outcome,
        "quest": quest,
        "xp": xp,
        "source": source,
    }


# Mad-Libs style: humor is fine, but every template names the real tool
# so the flavor text still actually says why the XP was awarded.
TICK_FLAVOR_TEMPLATES = [
    "wielded {tool} like a jedi lightsaber",
    "summoned {tool} from the depths",
    "high-fived {tool} for a job well done",
    "bravely deployed {tool} into unknown territory",
    "convinced {tool} to cooperate",
    "took {tool} out for a spin",
    "unleashed {tool} upon the codebase",
    "negotiated a peace treaty with {tool}",
    "performed advanced {tool} wizardry",
    "gave {tool} a stern talking-to",
    "tickled {tool} until it worked",
    "challenged {tool} to a duel and won",
    "recruited {tool} to the cause",
    "whispered sweet nothings to {tool}",
    "gave {tool} a run for its money",
    "yeeted {tool} directly at the problem",
    "bribed {tool} with a virtual cookie",
    "arm-wrestled {tool} into submission",
    "sent {tool} on a heroic quest",
    "taught {tool} a new trick",
    "coaxed {tool} out of hiding",
    "gave {tool} a pep talk",
    "fine-tuned {tool} with a wrench and a prayer",
    "let {tool} off its leash",
    "rode {tool} into battle",
    "consulted the ancient scrolls of {tool}",
    "did a victory lap with {tool}",
    "sharpened {tool} to a fine edge",
    "gave {tool} a gold star",
    "tuned {tool} like a fine instrument",
    "sent {tool} down the assembly line",
    "poked {tool} until it made noise",
    "cast a minor spell using {tool}",
    "drafted {tool} into the elite squad",
    "bribed the compiler with {tool}",
    "took {tool} for a test drive",
    "gave {tool} its moment to shine",
    "let {tool} do the heavy lifting",
    "put {tool} through its paces",
    "assembled the {tool} avengers",
    "invoked {tool} with great ceremony",
    "dusted off {tool} and got to work",
    "gave {tool} a firm handshake",
    "sicced {tool} on the bug",
    "let {tool} loose in the wild",
    "handed {tool} the keys to the kingdom",
    "gave {tool} a friendly nudge",
    "set {tool} to maximum overdrive",
    "carefully calibrated {tool}",
    "gave {tool} a well-earned coffee break after",
    "enlisted {tool} for a daring mission",
    "trusted {tool} with the crown jewels",
    "gave {tool} the green light",
    "let {tool} take the wheel",
    "spun up {tool} like a wizard",
    "gave {tool} a standing ovation",
    "put {tool} on the fast track",
    "gave {tool} a knighthood",
    "sent {tool} in to save the day",
    "gave {tool} a very important job",
    "unlocked {tool}'s true potential",
    "gave {tool} a turbo boost",
    "called in {tool} as backup",
    "gave {tool} the spotlight",
    "let {tool} flex its muscles",
    "gave {tool} a well-deserved promotion",
]

DEFAULT_TOOL_FILLER = "the tools"


def random_flavor(tool=None):
    template = random.choice(TICK_FLAVOR_TEMPLATES)
    return template.format(tool=tool or DEFAULT_TOOL_FILLER)


def new_tick_event(machine, xp=DEFAULT_TICK_XP, source="hook", flavor=None, tool=None):
    return {
        "event_id": str(uuid.uuid4()),
        "machine": machine,
        "ts": _now_iso(),
        "kind": "tick",
        "xp": xp,
        "source": source,
        "flavor": flavor if flavor is not None else random_flavor(tool),
    }


HISTORY_CAP = 100


def apply_event(ledger, event, history_cap=HISTORY_CAP):
    """Apply an award/tick event to ledger in place. Returns False (no-op)
    if event_id was already applied, True if it was newly applied."""
    if is_applied(ledger, event["event_id"]):
        return False

    old_level = level_for(ledger["total_xp"])
    ledger["total_xp"] += event["xp"]
    if event["kind"] == "award" and event.get("outcome") != "wipe":
        ledger["quests_completed"] += 1
    ledger["level"] = level_for(ledger["total_xp"])
    leveled_up = ledger["level"] > old_level

    entry = dict(event)
    entry["leveled_up"] = leveled_up
    entry["new_level"] = ledger["level"]
    history = ledger.setdefault("history", [])
    history.append(entry)
    del history[:-history_cap]

    record_applied(ledger, event["event_id"])
    ledger["next_level_at"] = next_level_at(ledger["total_xp"])
    return True


TICK_FLUSH_INTERVAL = 10.0


def should_flush_ticks(
    pending_count, last_flush_ts, now_ts, interval=TICK_FLUSH_INTERVAL
):
    return pending_count > 0 and (now_ts - last_flush_ts) >= interval


def coalesce_ticks(events, machine):
    if not events:
        raise ValueError("coalesce_ticks requires at least one event")
    return {
        "event_id": str(uuid.uuid4()),
        "machine": machine,
        "ts": _now_iso(),
        "kind": "tick",
        "xp": sum(e["xp"] for e in events),
        "source": "hook",
        "count": len(events),
        "flavor": events[0].get("flavor", random_flavor()),
    }


def append_outbox(path, event):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(event) + "\n")


def read_outbox(path):
    path = Path(path)
    if not path.exists():
        return []
    events = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line:
            events.append(json.loads(line))
    return events


def remove_from_outbox(path, event_id):
    path = Path(path)
    if not path.exists():
        return
    remaining = [e for e in read_outbox(path) if e["event_id"] != event_id]
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        for event in remaining:
            f.write(json.dumps(event) + "\n")
    os.replace(tmp, path)


MQTT_BROKER_HOST = "<broker-host>.<tailnet>.ts.net"
MQTT_TOPIC = "sidequest/xp/events"
MQTT_PUBLISH_TIMEOUT = 3


def publish_event(
    event,
    host=MQTT_BROKER_HOST,
    topic=MQTT_TOPIC,
    timeout=MQTT_PUBLISH_TIMEOUT,
    mosquitto_pub_cmd="mosquitto_pub",
):
    """Publish event to the MQTT broker. Returns True on success, False on
    any failure (broker unreachable, timeout, binary missing) — never
    raises, since a flaky broker must never crash the caller."""
    try:
        result = subprocess.run(
            [
                mosquitto_pub_cmd,
                "-h",
                host,
                "-t",
                topic,
                "-q",
                "1",
                "-m",
                json.dumps(event),
            ],
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


MQTT_STATE_TOPIC = "sidequest/xp/state"


def publish_state(
    ledger,
    machine,
    host=MQTT_BROKER_HOST,
    topic=MQTT_STATE_TOPIC,
    timeout=MQTT_PUBLISH_TIMEOUT,
    mosquitto_pub_cmd="mosquitto_pub",
):
    """Publish a retained snapshot of the current shared total. This is an
    observability/bootstrap convenience, not the source of truth for
    merging — the event stream (publish_event) is what keeps totals
    consistent across machines. A retained message means any client that
    connects (including one joining sync for the first time) gets the
    last known total immediately, without waiting for the next event."""
    payload = {
        "machine": machine,
        "ts": _now_iso(),
        "total_xp": ledger.get("total_xp", 0),
        "level": ledger.get("level", 1),
        "quests_completed": ledger.get("quests_completed", 0),
        "next_level_at": ledger.get("next_level_at"),
    }
    try:
        result = subprocess.run(
            [
                mosquitto_pub_cmd,
                "-h",
                host,
                "-t",
                topic,
                "-q",
                "1",
                "-r",
                "-m",
                json.dumps(payload),
            ],
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _empty_ledger():
    return {
        "total_xp": 0,
        "level": 1,
        "quests_completed": 0,
        "history": [],
        "applied_event_ids": [],
    }


def load_ledger(path):
    path = Path(path)
    if path.exists():
        return json.loads(path.read_text())
    return _empty_ledger()


def save_ledger(path, ledger):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump(ledger, f, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def is_applied(ledger, event_id):
    return event_id in ledger.get("applied_event_ids", [])


def record_applied(ledger, event_id, cap=APPLIED_EVENT_IDS_CAP):
    ids = ledger.setdefault("applied_event_ids", [])
    ids.append(event_id)
    del ids[:-cap]


# --- CLI ---------------------------------------------------------------
# Thin dispatch over the pure/testable functions above. Paths and the
# local machine name are read from the environment (with sensible
# defaults) so tests can redirect them without touching the real ledger.

import socket
import sys


def _side_quest_dir():
    return Path(os.environ.get("XP_HOME", str(Path.home() / ".claude" / "side-quest")))


def _ledger_path():
    return Path(os.environ.get("XP_LEDGER_PATH", str(_side_quest_dir() / "xp.json")))


def _outbox_path():
    return Path(
        os.environ.get("XP_OUTBOX_PATH", str(_side_quest_dir() / "mqtt_outbox.jsonl"))
    )


def _pending_ticks_path():
    return Path(
        os.environ.get(
            "XP_PENDING_TICKS_PATH", str(_side_quest_dir() / "pending_ticks.jsonl")
        )
    )


def _machine_name():
    return os.environ.get("XP_MACHINE", socket.gethostname().split(".")[0])


def _mosquitto_pub_cmd():
    return os.environ.get("MOSQUITTO_PUB_CMD", "mosquitto_pub")


def _publish_or_outbox(event):
    """Try to publish immediately; queue to the outbox on any failure."""
    if not publish_event(event, mosquitto_pub_cmd=_mosquitto_pub_cmd()):
        append_outbox(_outbox_path(), event)


def _publish_state_best_effort(ledger):
    """Publish the retained total-XP snapshot. Best-effort only — unlike
    events, a missed state update is superseded by the next one, so
    there's no outbox for this."""
    publish_state(ledger, _machine_name(), mosquitto_pub_cmd=_mosquitto_pub_cmd())


def cmd_award(argv):
    if len(argv) < 2:
        print(
            "usage: xp.sh award <cr> <success|partial|wipe> [--source X] <quest...>",
            file=sys.stderr,
        )
        sys.exit(2)
    cr = max(1, min(10, int(argv[0])))
    outcome = argv[1]
    if outcome not in ("success", "partial", "wipe"):
        print(f"unknown outcome: {outcome}", file=sys.stderr)
        sys.exit(2)
    rest = argv[2:]
    source = "ambient"
    if len(rest) >= 2 and rest[0] == "--source":
        source = rest[1]
        rest = rest[2:]
    quest = " ".join(rest) or "Unnamed quest"

    ledger = load_ledger(_ledger_path())
    event = new_award_event(_machine_name(), cr, outcome, quest, source=source)
    apply_event(ledger, event)
    save_ledger(_ledger_path(), ledger)
    _publish_or_outbox(event)
    _publish_state_best_effort(ledger)

    entry = ledger["history"][-1]
    print(
        json.dumps(
            {
                "awarded": event["xp"],
                "total_xp": ledger["total_xp"],
                "level": ledger["level"],
                "leveled_up": entry["leveled_up"],
                "quests_completed": ledger["quests_completed"],
                "next_level_at": ledger.get("next_level_at"),
            }
        )
    )


def cmd_tick(argv):
    tool = argv[0] if argv and argv[0] else None
    ledger = load_ledger(_ledger_path())
    event = new_tick_event(_machine_name(), tool=tool)
    apply_event(ledger, event)
    save_ledger(_ledger_path(), ledger)
    # Cross-machine publish is coalesced/batched by the sync daemon, not
    # done here — this must stay fast since it runs on every tool call.
    append_outbox(_pending_ticks_path(), event)


def cmd_status(argv):
    ledger = load_ledger(_ledger_path())
    ledger["level"] = level_for(ledger["total_xp"])
    ledger["next_level_at"] = next_level_at(ledger["total_xp"])
    save_ledger(_ledger_path(), ledger)
    print(
        json.dumps(
            {
                "total_xp": ledger["total_xp"],
                "level": ledger["level"],
                "quests_completed": ledger["quests_completed"],
                "next_level_at": ledger["next_level_at"],
            }
        )
    )


def cmd_statusline(argv):
    ledger = load_ledger(_ledger_path())
    print(f"⚔️ Lv {ledger['level']} · {ledger['total_xp']:,} XP")


def cmd_apply_remote(argv):
    """Apply an event received from MQTT. Reads JSON from argv[0], or
    stdin if argv is empty / '-'. Used by the listener daemon."""
    raw = argv[0] if argv and argv[0] != "-" else sys.stdin.read()
    event = json.loads(raw)
    ledger = load_ledger(_ledger_path())
    apply_event(ledger, event)
    save_ledger(_ledger_path(), ledger)
    _publish_state_best_effort(ledger)


def cmd_flush_outbox(argv):
    """Retry every queued event; drop only the ones that publish. Called
    by the daemon on every (re)connect."""
    flushed = 0
    for event in read_outbox(_outbox_path()):
        if publish_event(event, mosquitto_pub_cmd=_mosquitto_pub_cmd()):
            remove_from_outbox(_outbox_path(), event["event_id"])
            flushed += 1
    print(json.dumps({"flushed": flushed}))


def cmd_flush_ticks(argv):
    """Coalesce and publish pending ticks as one event. Called
    periodically by the daemon; the daemon's own poll interval enforces
    the batching window (see TICK_FLUSH_INTERVAL)."""
    pending = read_outbox(_pending_ticks_path())
    if not pending:
        print(json.dumps({"flushed": 0}))
        return

    combined = coalesce_ticks(pending, _machine_name())
    ledger = load_ledger(_ledger_path())
    # Already applied locally as individual ticks — only mark the
    # coalesced id as seen so a future echo of it is ignored, never
    # re-add its xp.
    record_applied(ledger, combined["event_id"])
    save_ledger(_ledger_path(), ledger)
    _publish_or_outbox(combined)
    _publish_state_best_effort(ledger)

    _pending_ticks_path().write_text("")
    print(json.dumps({"flushed": len(pending), "combined_xp": combined["xp"]}))


COMMANDS = {
    "award": cmd_award,
    "tick": cmd_tick,
    "status": cmd_status,
    "statusline": cmd_statusline,
    "apply-remote": cmd_apply_remote,
    "flush-outbox": cmd_flush_outbox,
    "flush-ticks": cmd_flush_ticks,
}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    cmd = argv[0] if argv else "status"
    handler = COMMANDS.get(cmd)
    if handler is None:
        print(f"unknown command: {cmd}", file=sys.stderr)
        sys.exit(2)
    handler(argv[1:])


if __name__ == "__main__":
    main()
