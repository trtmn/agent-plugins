from xp_core import (
    LEVEL_AWARD_GROWTH,
    TICK_FLAVOR_TEMPLATES,
    ZERO_TOOL_FLAVOR_TEMPLATES,
    append_outbox,
    apply_bootstrap,
    apply_event,
    coalesce_ticks,
    count_hook_entries_since,
    is_applied,
    level_for,
    load_ledger,
    new_award_event,
    new_response_event,
    new_tick_event,
    next_level_at,
    publish_event,
    publish_state,
    random_flavor,
    random_zero_tool_flavor,
    read_outbox,
    record_applied,
    remove_from_outbox,
    save_ledger,
    should_bootstrap_from_state,
    should_flush_ticks,
    xp_for_tool_count,
)


def _empty_ledger():
    return {
        "total_xp": 0,
        "level": 1,
        "quests_completed": 0,
        "history": [],
        "applied_event_ids": [],
    }


def test_is_applied_false_for_unknown_event():
    ledger = {"applied_event_ids": []}
    assert is_applied(ledger, "evt-1") is False


def test_record_applied_marks_event_as_applied():
    ledger = {"applied_event_ids": []}
    record_applied(ledger, "evt-1")
    assert is_applied(ledger, "evt-1") is True


def test_record_applied_caps_ring_buffer_dropping_oldest():
    ledger = {"applied_event_ids": []}
    for i in range(5):
        record_applied(ledger, f"evt-{i}", cap=3)
    assert ledger["applied_event_ids"] == ["evt-2", "evt-3", "evt-4"]


def test_new_award_event_uses_xp_by_cr_table_for_success():
    event = new_award_event(
        machine="machine-a", cr=3, outcome="success", quest="fix bug"
    )
    assert event["xp"] == 7000
    assert event["kind"] == "award"
    assert event["machine"] == "machine-a"
    assert event["cr"] == 3
    assert event["outcome"] == "success"
    assert event["quest"] == "fix bug"
    assert event["event_id"]
    assert event["ts"]


def test_new_award_event_halves_xp_for_partial():
    event = new_award_event(
        machine="machine-a", cr=3, outcome="partial", quest="fix bug"
    )
    assert event["xp"] == 3500


def test_new_award_event_zero_xp_for_wipe():
    event = new_award_event(machine="machine-a", cr=3, outcome="wipe", quest="fix bug")
    assert event["xp"] == 0


def test_new_award_event_scales_up_with_level():
    lvl1 = new_award_event(machine="m", cr=3, outcome="success", quest="x", level=1)
    lvl10 = new_award_event(machine="m", cr=3, outcome="success", quest="x", level=10)
    assert lvl1["xp"] == 7000
    # 7000 * 1.04**9 ≈ 9962
    assert lvl10["xp"] == round(7000 * 1.04**9)
    assert lvl10["xp"] > lvl1["xp"]


def test_new_award_event_level_growth_trails_threshold_growth():
    # awards grow at 1.04/level, thresholds at 1.05 — awards must lag
    assert LEVEL_AWARD_GROWTH < 1.05


def test_new_award_event_ids_are_unique():
    a = new_award_event(machine="machine-a", cr=1, outcome="success", quest="x")
    b = new_award_event(machine="machine-a", cr=1, outcome="success", quest="x")
    assert a["event_id"] != b["event_id"]


def test_new_tick_event_defaults():
    event = new_tick_event(machine="machine-a")
    assert event["kind"] == "tick"
    assert event["xp"] == 10
    assert event["machine"] == "machine-a"
    assert event["source"] == "hook"
    assert event["event_id"]


def test_new_tick_event_includes_a_flavor_mentioning_the_tool_used():
    event = new_tick_event(machine="machine-a", tool="Grep")
    assert "Grep" in event["flavor"]


def test_new_tick_event_flavor_varies_by_template_but_always_names_the_tool():
    # every template must actually name the real tool -- that's the part
    # the user asked for explicitly: humor is fine, but it must still say
    # why the XP was awarded.
    seen = {
        new_tick_event(machine="machine-a", tool="Bash")["flavor"] for _ in range(50)
    }
    assert len(seen) > 1  # got some actual variety, not always the same template
    assert all("Bash" in flavor for flavor in seen)


def test_new_tick_event_uses_generic_filler_when_tool_unknown():
    event = new_tick_event(machine="machine-a", tool=None)
    assert event["flavor"]  # still produces something sensible


def test_new_tick_event_respects_explicit_flavor_override():
    event = new_tick_event(machine="machine-a", flavor="did something specific")
    assert event["flavor"] == "did something specific"


def test_random_flavor_fills_in_the_given_tool_name():
    flavor = random_flavor("Edit")
    assert "Edit" in flavor


def test_random_flavor_templates_all_contain_a_tool_placeholder():
    assert len(TICK_FLAVOR_TEMPLATES) >= 100
    assert all("{tool}" in t for t in TICK_FLAVOR_TEMPLATES)


def test_xp_for_tool_count_gives_at_least_the_floor_for_zero_tools():
    assert xp_for_tool_count(0) == 100


def test_xp_for_tool_count_never_goes_below_the_floor():
    for n in range(100):
        assert xp_for_tool_count(n) >= 100


def test_xp_for_tool_count_increases_with_more_tool_calls():
    assert xp_for_tool_count(1) > xp_for_tool_count(0)
    assert xp_for_tool_count(5) > xp_for_tool_count(1)
    assert xp_for_tool_count(20) > xp_for_tool_count(5)


def test_count_hook_entries_since_counts_only_tick_sourced_entries_after_boundary():
    history = [
        {"source": "hook", "ts": "2026-08-07T21:00:00+00:00"},
        {"source": "ambient", "ts": "2026-08-07T21:00:05+00:00"},
        {"source": "hook", "ts": "2026-08-07T21:00:10+00:00"},
        {"source": "hook", "ts": "2026-08-07T21:00:15+00:00"},
    ]
    count = count_hook_entries_since(history, "2026-08-07T21:00:05+00:00")
    assert count == 2


def test_count_hook_entries_since_counts_everything_when_no_boundary():
    history = [
        {"source": "hook", "ts": "2026-08-07T21:00:00+00:00"},
        {"source": "hook", "ts": "2026-08-07T21:00:10+00:00"},
    ]
    assert count_hook_entries_since(history, None) == 2


def test_new_response_event_meets_the_floor_with_no_tool_calls():
    event = new_response_event(machine="machine-a", tool_count=0)
    assert event["xp"] == 100
    assert event["kind"] == "response"
    assert event["source"] == "stop-hook"


def test_new_response_event_scales_with_tool_count():
    event = new_response_event(machine="machine-a", tool_count=15)
    assert event["xp"] > 100


def test_new_response_event_scales_up_with_level():
    lvl1 = new_response_event(machine="m", tool_count=0, level=1)
    lvl5 = new_response_event(machine="m", tool_count=0, level=5)
    assert lvl1["xp"] == 100
    assert lvl5["xp"] == round(100 * LEVEL_AWARD_GROWTH**4)
    assert lvl5["xp"] > lvl1["xp"]


def test_new_response_event_uses_zero_tool_flavor_pool_for_no_tool_calls():
    event = new_response_event(machine="machine-a", tool_count=0)
    assert event["flavor"] in ZERO_TOOL_FLAVOR_TEMPLATES


def test_new_response_event_uses_tick_flavor_pool_when_tools_were_used():
    event = new_response_event(machine="machine-a", tool_count=3)
    possible = {t.format(tool="the crew") for t in TICK_FLAVOR_TEMPLATES}
    assert event["flavor"] in possible


def test_random_zero_tool_flavor_returns_a_template_from_the_pool():
    assert random_zero_tool_flavor() in ZERO_TOOL_FLAVOR_TEMPLATES


def test_zero_tool_flavor_templates_are_all_unique():
    assert len(ZERO_TOOL_FLAVOR_TEMPLATES) == len(set(ZERO_TOOL_FLAVOR_TEMPLATES))


def test_should_bootstrap_from_state_true_for_fresh_ledger_with_higher_state():
    ledger = _empty_ledger()
    state = {"total_xp": 818000, "level": 78, "quests_completed": 2500}
    assert should_bootstrap_from_state(ledger, state) is True


def test_should_bootstrap_from_state_false_when_ledger_already_has_xp():
    ledger = _empty_ledger()
    ledger["total_xp"] = 50
    ledger["history"] = [{"kind": "tick", "xp": 50}]
    state = {"total_xp": 818000}
    assert should_bootstrap_from_state(ledger, state) is False


def test_should_bootstrap_from_state_false_when_state_total_is_zero():
    ledger = _empty_ledger()
    state = {"total_xp": 0}
    assert should_bootstrap_from_state(ledger, state) is False


def test_should_bootstrap_from_state_false_when_state_missing():
    ledger = _empty_ledger()
    assert should_bootstrap_from_state(ledger, None) is False


def test_apply_bootstrap_adopts_the_state_totals():
    ledger = _empty_ledger()
    state = {
        "total_xp": 818000,
        "level": 78,
        "quests_completed": 2500,
        "next_level_at": 824000,
    }
    apply_bootstrap(ledger, state, machine="machine-b")
    assert ledger["total_xp"] == 818000
    assert ledger["level"] == 78
    assert ledger["quests_completed"] == 2500
    assert ledger["next_level_at"] == 824000


def test_apply_bootstrap_does_not_double_count_on_replay():
    ledger = _empty_ledger()
    state = {"total_xp": 818000, "level": 78, "quests_completed": 2500}
    apply_bootstrap(ledger, state, machine="machine-b")
    # a second bootstrap attempt against an already-bootstrapped ledger
    # must be a caller-level no-op, guarded by should_bootstrap_from_state
    assert should_bootstrap_from_state(ledger, state) is False


def test_apply_bootstrap_records_a_history_entry(tmp_path=None):
    ledger = _empty_ledger()
    state = {"total_xp": 818000, "level": 78, "quests_completed": 2500}
    apply_bootstrap(ledger, state, machine="machine-b")
    assert len(ledger["history"]) == 1
    assert ledger["history"][0]["kind"] == "bootstrap"
    assert ledger["history"][0]["xp"] == 0  # adopting, not earning new XP


def test_flavor_templates_are_all_unique():
    # duplicates would silently shrink the effective variety
    assert len(TICK_FLAVOR_TEMPLATES) == len(set(TICK_FLAVOR_TEMPLATES))


def test_level_for_zero_xp_is_level_one():
    assert level_for(0) == 1


def test_level_for_below_first_threshold_is_level_one():
    assert level_for(999) == 1


def test_level_for_at_first_threshold_is_level_two():
    assert level_for(1000) == 2


def test_next_level_at_zero_xp_is_first_threshold():
    assert next_level_at(0) == 1000


def test_next_level_at_returns_none_never():
    # thresholds are built past any given xp, so there's always a next one
    assert next_level_at(50000) is not None


def test_apply_event_adds_xp_to_total():
    ledger = _empty_ledger()
    event = new_award_event(machine="machine-a", cr=1, outcome="success", quest="x")
    applied = apply_event(ledger, event)
    assert applied is True
    assert ledger["total_xp"] == 2000


def test_apply_event_is_idempotent_for_duplicate_event_id():
    ledger = _empty_ledger()
    event = new_award_event(machine="machine-a", cr=1, outcome="success", quest="x")
    apply_event(ledger, event)
    applied_again = apply_event(ledger, event)
    assert applied_again is False
    assert ledger["total_xp"] == 2000


def test_apply_event_increments_quests_completed_for_award_success():
    ledger = _empty_ledger()
    event = new_award_event(machine="machine-a", cr=1, outcome="success", quest="x")
    apply_event(ledger, event)
    assert ledger["quests_completed"] == 1


def test_apply_event_does_not_increment_quests_completed_for_wipe():
    ledger = _empty_ledger()
    event = new_award_event(machine="machine-a", cr=1, outcome="wipe", quest="x")
    apply_event(ledger, event)
    assert ledger["quests_completed"] == 0


def test_apply_event_does_not_increment_quests_completed_for_tick():
    ledger = _empty_ledger()
    event = new_tick_event(machine="machine-a")
    apply_event(ledger, event)
    assert ledger["quests_completed"] == 0
    assert ledger["total_xp"] == 10


def test_apply_event_appends_history_entry_with_machine_and_event_id():
    ledger = _empty_ledger()
    event = new_award_event(machine="machine-a", cr=1, outcome="success", quest="x")
    apply_event(ledger, event)
    assert len(ledger["history"]) == 1
    entry = ledger["history"][0]
    assert entry["event_id"] == event["event_id"]
    assert entry["machine"] == "machine-a"
    assert entry["xp"] == 2000


def test_apply_event_marks_event_id_as_applied():
    ledger = _empty_ledger()
    event = new_award_event(machine="machine-a", cr=1, outcome="success", quest="x")
    apply_event(ledger, event)
    assert is_applied(ledger, event["event_id"]) is True


def test_apply_event_detects_level_up():
    ledger = _empty_ledger()
    # CR 1 success = 2000 XP, past the 1000 XP level-2 threshold
    event = new_award_event(machine="machine-a", cr=1, outcome="success", quest="x")
    apply_event(ledger, event)
    assert ledger["level"] == 2
    assert ledger["history"][0]["leveled_up"] is True


def test_apply_event_no_level_up_when_still_under_threshold():
    ledger = _empty_ledger()
    event = new_tick_event(machine="machine-a")  # 10 XP, well under 1000
    apply_event(ledger, event)
    assert ledger["level"] == 1
    assert ledger["history"][0]["leveled_up"] is False


def test_apply_event_carries_tick_flavor_into_history_entry():
    ledger = _empty_ledger()
    event = new_tick_event(machine="machine-a", flavor="poked a semicolon")
    apply_event(ledger, event)
    assert ledger["history"][0]["flavor"] == "poked a semicolon"


def test_apply_event_caps_history_length():
    ledger = _empty_ledger()
    for i in range(5):
        event = new_tick_event(machine="machine-a")
        apply_event(ledger, event, history_cap=3)
    assert len(ledger["history"]) == 3


def test_should_flush_ticks_false_when_no_pending():
    assert should_flush_ticks(pending_count=0, last_flush_ts=0, now_ts=100) is False


def test_should_flush_ticks_false_before_interval_elapsed():
    assert (
        should_flush_ticks(pending_count=3, last_flush_ts=100, now_ts=105, interval=10)
        is False
    )


def test_should_flush_ticks_true_after_interval_elapsed():
    assert (
        should_flush_ticks(pending_count=3, last_flush_ts=100, now_ts=111, interval=10)
        is True
    )


def test_coalesce_ticks_sums_xp_into_one_tick_event():
    ticks = [new_tick_event(machine="machine-a", xp=10) for _ in range(3)]
    combined = coalesce_ticks(ticks, machine="machine-a")
    assert combined["xp"] == 30
    assert combined["kind"] == "tick"
    assert combined["machine"] == "machine-a"
    assert combined["event_id"] not in {t["event_id"] for t in ticks}


def test_coalesce_ticks_uses_the_first_ticks_flavor_for_the_batch():
    ticks = [
        new_tick_event(machine="machine-a", flavor="first flavor"),
        new_tick_event(machine="machine-a", flavor="second flavor"),
    ]
    combined = coalesce_ticks(ticks, machine="machine-a")
    assert combined["flavor"] == "first flavor"


def test_coalesce_ticks_raises_on_empty_list():
    import pytest

    with pytest.raises(ValueError):
        coalesce_ticks([], machine="machine-a")


def test_read_outbox_empty_when_file_missing(tmp_path):
    path = tmp_path / "outbox.jsonl"
    assert read_outbox(path) == []


def test_append_outbox_then_read_returns_event(tmp_path):
    path = tmp_path / "outbox.jsonl"
    event = new_tick_event(machine="machine-a")
    append_outbox(path, event)
    events = read_outbox(path)
    assert len(events) == 1
    assert events[0]["event_id"] == event["event_id"]


def test_append_outbox_preserves_order_across_multiple_events(tmp_path):
    path = tmp_path / "outbox.jsonl"
    events = [new_tick_event(machine="machine-a") for _ in range(3)]
    for e in events:
        append_outbox(path, e)
    read_back = read_outbox(path)
    assert [e["event_id"] for e in read_back] == [e["event_id"] for e in events]


def test_remove_from_outbox_drops_only_matching_event(tmp_path):
    path = tmp_path / "outbox.jsonl"
    events = [new_tick_event(machine="machine-a") for _ in range(3)]
    for e in events:
        append_outbox(path, e)
    remove_from_outbox(path, events[1]["event_id"])
    remaining_ids = [e["event_id"] for e in read_outbox(path)]
    assert remaining_ids == [events[0]["event_id"], events[2]["event_id"]]


def test_remove_from_outbox_on_missing_file_is_a_noop(tmp_path):
    path = tmp_path / "outbox.jsonl"
    remove_from_outbox(path, "nonexistent")  # must not raise
    assert read_outbox(path) == []


def test_load_ledger_returns_empty_default_when_file_missing(tmp_path):
    path = tmp_path / "xp.json"
    ledger = load_ledger(path)
    assert ledger == _empty_ledger()


def test_save_then_load_ledger_roundtrips(tmp_path):
    path = tmp_path / "xp.json"
    ledger = _empty_ledger()
    event = new_award_event(machine="machine-a", cr=1, outcome="success", quest="x")
    apply_event(ledger, event)
    save_ledger(path, ledger)
    reloaded = load_ledger(path)
    assert reloaded["total_xp"] == 2000
    assert reloaded["history"][0]["event_id"] == event["event_id"]


def _write_fake_mosquitto_pub(tmp_path, exit_code):
    script = tmp_path / "mosquitto_pub"
    script.write_text(f"#!/bin/sh\nexit {exit_code}\n")
    script.chmod(0o755)
    return str(script)


def test_publish_event_returns_true_on_success(tmp_path):
    fake_bin = _write_fake_mosquitto_pub(tmp_path, exit_code=0)
    event = new_tick_event(machine="machine-a")
    assert publish_event(event, host="test-broker", mosquitto_pub_cmd=fake_bin) is True


def test_publish_event_returns_false_on_failure(tmp_path):
    fake_bin = _write_fake_mosquitto_pub(tmp_path, exit_code=1)
    event = new_tick_event(machine="machine-a")
    assert publish_event(event, host="test-broker", mosquitto_pub_cmd=fake_bin) is False


def test_publish_event_returns_false_when_binary_missing(tmp_path):
    missing = str(tmp_path / "does-not-exist")
    event = new_tick_event(machine="machine-a")
    assert publish_event(event, host="test-broker", mosquitto_pub_cmd=missing) is False


def test_publish_state_returns_true_on_success(tmp_path):
    fake_bin = _write_fake_mosquitto_pub(tmp_path, exit_code=0)
    ledger = _empty_ledger()
    assert (
        publish_state(
            ledger, machine="machine-a", host="test-broker", mosquitto_pub_cmd=fake_bin
        )
        is True
    )


def test_publish_state_returns_false_on_failure(tmp_path):
    fake_bin = _write_fake_mosquitto_pub(tmp_path, exit_code=1)
    ledger = _empty_ledger()
    assert (
        publish_state(
            ledger, machine="machine-a", host="test-broker", mosquitto_pub_cmd=fake_bin
        )
        is False
    )


def test_publish_state_passes_the_retain_flag(tmp_path):
    # the state topic must be retained so a machine that just connected
    # (or joined for the first time) gets the current total immediately,
    # without waiting for the next event.
    spy_log = tmp_path / "argv.log"
    spy = tmp_path / "mosquitto_pub"
    spy.write_text(f'#!/bin/sh\necho "$@" >> "{spy_log}"\nexit 0\n')
    spy.chmod(0o755)
    ledger = _empty_ledger()
    publish_state(
        ledger, machine="machine-a", host="test-broker", mosquitto_pub_cmd=str(spy)
    )
    argv = spy_log.read_text()
    assert " -r " in f" {argv} "


def test_publish_state_payload_includes_total_xp_and_machine(tmp_path):
    spy_log = tmp_path / "argv.log"
    spy = tmp_path / "mosquitto_pub"
    spy.write_text(f'#!/bin/sh\necho "$@" >> "{spy_log}"\nexit 0\n')
    spy.chmod(0o755)
    ledger = _empty_ledger()
    ledger["total_xp"] = 12345
    ledger["level"] = 9
    publish_state(
        ledger, machine="machine-a", host="test-broker", mosquitto_pub_cmd=str(spy)
    )
    argv = spy_log.read_text()
    assert "12345" in argv
    assert '"machine-a"' in argv


def test_publish_event_does_not_pass_flags_mosquitto_pub_rejects(tmp_path):
    # mosquitto_pub has no -W flag (that's mosquitto_sub's wait-for-message
    # timeout) -- a real broker round trip caught this: publish_event used
    # to pass -W and every real publish silently failed and fell through
    # to the outbox. Spy script records argv and rejects unknown flags,
    # the same way the real binary does.
    spy = tmp_path / "mosquitto_pub"
    spy.write_text(
        "#!/bin/sh\n"
        'for arg in "$@"; do\n'
        '  case "$arg" in\n'
        "    -h|-t|-q|-m|-*) ;;\n"
        "  esac\n"
        "done\n"
        'case " $* " in\n'
        "  *' -W '*) echo \"Error: Unknown option '-W'.\" >&2; exit 1 ;;\n"
        "esac\n"
        "exit 0\n"
    )
    spy.chmod(0o755)
    event = new_tick_event(machine="machine-a")
    assert publish_event(event, host="test-broker", mosquitto_pub_cmd=str(spy)) is True
