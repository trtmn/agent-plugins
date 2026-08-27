import json
import os
import subprocess
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
XP_SH = SCRIPTS_DIR / "xp.sh"


def _write_fake_pub(home, exit_code=0):
    fake_pub = home / "fake_mosquitto_pub"
    fake_pub.write_text(f"#!/bin/sh\nexit {exit_code}\n")
    fake_pub.chmod(0o755)
    return fake_pub


def _write_spy_pub(home):
    fake_pub = home / "fake_mosquitto_pub"
    log = home / "pub_argv.log"
    fake_pub.write_text(f'#!/bin/sh\necho "$@" >> "{log}"\nexit 0\n')
    fake_pub.chmod(0o755)
    return log


def _run(args, home, extra_env=None, stdin_data=None):
    if not (home / "fake_mosquitto_pub").exists():
        _write_fake_pub(home, exit_code=0)
    env = {
        **os.environ,
        "XP_HOME": str(home),
        "MOSQUITTO_PUB_CMD": str(home / "fake_mosquitto_pub"),
        "XP_MQTT_HOST": "test-broker.invalid",
        **(extra_env or {}),
    }
    return subprocess.run(
        ["bash", str(XP_SH), *args],
        env=env,
        input=stdin_data if stdin_data is not None else "",
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )


def test_award_writes_ledger_and_prints_summary(tmp_path):
    result = _run(["award", "3", "success", "fix the thing"], home=tmp_path)
    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    assert summary["awarded"] == 7000
    assert summary["total_xp"] == 7000

    ledger = json.loads((tmp_path / "xp.json").read_text())
    assert ledger["total_xp"] == 7000
    assert ledger["quests_completed"] == 1


def test_tick_updates_ledger_silently_and_queues_for_daemon(tmp_path):
    result = _run(["tick"], home=tmp_path)
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""

    ledger = json.loads((tmp_path / "xp.json").read_text())
    assert ledger["total_xp"] == 10
    assert ledger["quests_completed"] == 0

    pending = (tmp_path / "pending_ticks.jsonl").read_text().strip().splitlines()
    assert len(pending) == 1


def test_tick_with_tool_name_names_it_in_the_flavor_text(tmp_path):
    result = _run(["tick", "Grep"], home=tmp_path)
    assert result.returncode == 0, result.stderr

    ledger = json.loads((tmp_path / "xp.json").read_text())
    assert "Grep" in ledger["history"][-1]["flavor"]


def test_award_respects_xp_mqtt_host_override(tmp_path):
    # some machines can't resolve the broker's MagicDNS hostname and
    # need to target it by raw Tailscale IP instead
    log = _write_spy_pub(tmp_path)
    result = _run(
        ["award", "1", "success", "host override test"],
        home=tmp_path,
        extra_env={"XP_MQTT_HOST": "100.99.99.99"},
    )
    assert result.returncode == 0, result.stderr
    calls = log.read_text().strip().splitlines()
    assert any("100.99.99.99" in c for c in calls)
    assert not any("test-broker.invalid" in c for c in calls)


def test_award_also_publishes_a_retained_state_snapshot(tmp_path):
    log = _write_spy_pub(tmp_path)
    result = _run(["award", "2", "success", "state snapshot test"], home=tmp_path)
    assert result.returncode == 0, result.stderr

    calls = log.read_text().strip().splitlines()
    state_calls = [c for c in calls if "sidequest/xp/state" in c]
    assert len(state_calls) == 1
    assert " -r " in f" {state_calls[0]} "
    assert "450" in state_calls[0]  # CR2 success xp


def test_award_queues_to_outbox_when_broker_unreachable(tmp_path):
    _write_fake_pub(tmp_path, exit_code=1)
    result = _run(["award", "1", "success", "offline quest"], home=tmp_path)
    assert result.returncode == 0, result.stderr

    # local ledger still updates even though the publish failed
    ledger = json.loads((tmp_path / "xp.json").read_text())
    assert ledger["total_xp"] == 2000

    outbox = (tmp_path / "mqtt_outbox.jsonl").read_text().strip().splitlines()
    assert len(outbox) == 1
    queued = json.loads(outbox[0])
    assert queued["xp"] == 2000


def test_flush_outbox_removes_events_that_publish_successfully(tmp_path):
    _write_fake_pub(tmp_path, exit_code=1)
    _run(["award", "1", "success", "offline quest"], home=tmp_path)
    assert (tmp_path / "mqtt_outbox.jsonl").read_text().strip() != ""

    _write_fake_pub(tmp_path, exit_code=0)
    result = _run(["flush-outbox"], home=tmp_path)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["flushed"] == 1
    assert (tmp_path / "mqtt_outbox.jsonl").read_text().strip() == ""


def test_flush_ticks_coalesces_pending_ticks_into_one_publish(tmp_path):
    for _ in range(3):
        _run(["tick"], home=tmp_path)
    result = _run(["flush-ticks"], home=tmp_path)
    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    assert summary["flushed"] == 3
    assert summary["combined_xp"] == 30
    assert (tmp_path / "pending_ticks.jsonl").read_text().strip() == ""

    # local total is unaffected by the flush (ticks already applied
    # individually at tick time) — no double counting
    ledger = json.loads((tmp_path / "xp.json").read_text())
    assert ledger["total_xp"] == 30


def test_flush_ticks_is_a_noop_when_nothing_pending(tmp_path):
    result = _run(["flush-ticks"], home=tmp_path)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["flushed"] == 0


def test_respond_awards_the_floor_when_no_tool_calls_happened(tmp_path):
    result = _run(["respond"], home=tmp_path)
    assert result.returncode == 0, result.stderr
    ledger = json.loads((tmp_path / "xp.json").read_text())
    assert ledger["total_xp"] == 100
    assert ledger["history"][-1]["kind"] == "response"


def test_respond_scales_up_with_prior_tick_count(tmp_path):
    for _ in range(6):
        _run(["tick"], home=tmp_path)
    result = _run(["respond"], home=tmp_path)
    assert result.returncode == 0, result.stderr
    ledger = json.loads((tmp_path / "xp.json").read_text())
    # 6 ticks * 10xp + response reward for a 6-tool-call turn (tier > 10xp)
    assert ledger["total_xp"] == 60 + 800


def test_respond_does_not_bump_quests_completed(tmp_path):
    _run(["respond"], home=tmp_path)
    ledger = json.loads((tmp_path / "xp.json").read_text())
    assert ledger["quests_completed"] == 0


def test_respond_is_debounced_right_after_an_ambient_award(tmp_path):
    _run(["award", "1", "success", "just did a thing"], home=tmp_path)
    before = json.loads((tmp_path / "xp.json").read_text())["total_xp"]

    result = _run(["respond"], home=tmp_path)
    assert result.returncode == 0, result.stderr
    after = json.loads((tmp_path / "xp.json").read_text())["total_xp"]
    assert after == before  # skipped -- the model's own award already covered this turn


def test_bootstrap_adopts_state_on_a_fresh_ledger(tmp_path):
    state = {"total_xp": 818000, "level": 78, "quests_completed": 2500}
    result = _run(["bootstrap", json.dumps(state)], home=tmp_path)
    assert result.returncode == 0, result.stderr

    ledger = json.loads((tmp_path / "xp.json").read_text())
    assert ledger["total_xp"] == 818000
    assert ledger["history"][-1]["kind"] == "bootstrap"


def test_bootstrap_is_a_noop_on_a_ledger_that_already_has_xp(tmp_path):
    _run(["award", "1", "success", "already earning locally"], home=tmp_path)
    before = json.loads((tmp_path / "xp.json").read_text())["total_xp"]

    state = {"total_xp": 818000}
    _run(["bootstrap", json.dumps(state)], home=tmp_path)

    after = json.loads((tmp_path / "xp.json").read_text())["total_xp"]
    assert after == before  # must not clobber real local earnings


def test_bootstrap_handles_empty_input_gracefully(tmp_path):
    result = _run(["bootstrap", ""], home=tmp_path)
    assert result.returncode == 0, result.stderr


def test_apply_remote_event_updates_ledger(tmp_path):
    event = {
        "event_id": "remote-evt-1",
        "machine": "machine-b",
        "ts": "2026-08-07T20:00:00Z",
        "kind": "award",
        "cr": 2,
        "outcome": "success",
        "quest": "remote work",
        "xp": 450,
        "source": "ambient",
    }
    result = _run(["apply-remote", json.dumps(event)], home=tmp_path)
    assert result.returncode == 0, result.stderr

    ledger = json.loads((tmp_path / "xp.json").read_text())
    assert ledger["total_xp"] == 450
    assert ledger["history"][0]["machine"] == "machine-b"


def test_apply_remote_event_is_idempotent_on_replay(tmp_path):
    event = {
        "event_id": "remote-evt-2",
        "machine": "machine-b",
        "ts": "2026-08-07T20:00:00Z",
        "kind": "tick",
        "xp": 10,
        "source": "hook",
    }
    _run(["apply-remote", json.dumps(event)], home=tmp_path)
    _run(["apply-remote", json.dumps(event)], home=tmp_path)

    ledger = json.loads((tmp_path / "xp.json").read_text())
    assert ledger["total_xp"] == 10


def test_apply_remote_ignores_our_own_echoed_event(tmp_path):
    # the broker echoes our publishes back to our own subscriber; we
    # already applied them locally, so re-applying only risks a
    # double-count once the id ages out of the dedup ring.
    event = {
        "event_id": "self-echo-1",
        "machine": "thisbox",
        "ts": "2026-08-27T00:00:00+00:00",
        "kind": "response",
        "xp": 5000,
        "source": "stop-hook",
    }
    _run(
        ["apply-remote", json.dumps(event)],
        home=tmp_path,
        extra_env={"XP_MACHINE": "thisbox"},
    )
    result = _run(["status"], home=tmp_path, extra_env={"XP_MACHINE": "thisbox"})
    assert json.loads(result.stdout)["total_xp"] == 0


def test_reconcile_catches_a_drifted_ledger_up_to_shared_state(tmp_path):
    _run(["award", "1", "success", "local earning"], home=tmp_path)
    before = json.loads((tmp_path / "xp.json").read_text())["total_xp"]
    state = {"total_xp": before + 500_000, "epoch": 0}
    _run(["reconcile", json.dumps(state)], home=tmp_path)
    after = json.loads((tmp_path / "xp.json").read_text())["total_xp"]
    assert after == before + 500_000
    assert (
        json.loads((tmp_path / "xp.json").read_text())["history"][-1]["kind"]
        == "reconcile"
    )


def test_reset_ledger_forces_total_and_bumps_epoch(tmp_path):
    _run(["award", "1", "success", "some xp"], home=tmp_path)
    result = _run(["reset-ledger", "12345"], home=tmp_path)
    out = json.loads(result.stdout)
    assert out["total_xp"] == 12345
    assert out["epoch"] == 1
    ledger = json.loads((tmp_path / "xp.json").read_text())
    assert ledger["total_xp"] == 12345
    assert ledger["epoch"] == 1


def test_respond_uses_the_transcript_heuristic_when_given_one(tmp_path):
    transcript = tmp_path / "t.jsonl"
    rows = [
        {"type": "user", "message": {"role": "user", "content": "do a big refactor"}},
        {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "name": "Edit",
                        "input": {
                            "file_path": f"/p/f{i}.py",
                            "old_string": "x" * 200,
                            "new_string": "y" * 200,
                        },
                    }
                    for i in range(9)
                ],
            },
        },
    ]
    transcript.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    _run(
        ["respond"],
        home=tmp_path,
        stdin_data=json.dumps({"transcript_path": str(transcript)}),
    )
    ledger = json.loads((tmp_path / "xp.json").read_text())
    entry = ledger["history"][-1]
    assert entry["kind"] == "response"
    assert entry["cr"] == 5  # 9 distinct files edited
    assert entry["xp"] == 18000  # CR5 base, level 1, no scaling
