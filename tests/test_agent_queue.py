import json

import pytest

from pro_ai_server.agent.queue import (
    build_decision_queue,
    current_decisions_from_events,
    default_decision_ledger_path,
    default_decision_path,
    load_decision_events,
    load_decisions,
    record_decision,
    render_decision_history,
    render_decision_queue,
    validate_decision,
)


def test_validate_decision_accepts_known_values():
    assert validate_decision("accepted") == "accepted"
    assert validate_decision("Deferred") == "deferred"
    assert validate_decision(" rejected ") == "rejected"


def test_validate_decision_rejects_unknown_value():
    with pytest.raises(ValueError, match="accepted, deferred, rejected"):
        validate_decision("maybe")


def test_record_decision_writes_deterministic_queue(tmp_path):
    ticket_dir = tmp_path / ".agents" / "build-tickets" / "phase-11"
    ticket_dir.mkdir(parents=True)
    ticket_path = ticket_dir / "TKT-P11-001-example.md"
    ticket_path.write_text("# Example", encoding="utf-8")

    record = record_decision("TKT-P11-001", decision="accepted", reason="Ready to implement.", root=tmp_path)

    assert record.ticket_path == ticket_path
    assert record.phase == "phase-11"
    payload = json.loads(default_decision_path(tmp_path).read_text(encoding="utf-8"))
    assert payload["decisions"][0]["ticket_id"] == "TKT-P11-001"
    assert payload["decisions"][0]["decision"] == "accepted"
    events = load_decision_events(default_decision_ledger_path(tmp_path))
    assert events[0].sequence == 1
    assert events[0].decision == "accepted"


def test_record_decision_updates_existing_ticket_decision(tmp_path):
    record_decision("TKT-P11-001", decision="deferred", reason="Needs context.", root=tmp_path)
    record_decision("TKT-P11-001", decision="accepted", reason="Context added.", root=tmp_path)

    decisions = load_decisions(default_decision_path(tmp_path))

    assert len(decisions) == 1
    assert decisions[0].decision == "accepted"
    assert decisions[0].reason == "Context added."
    events = load_decision_events(default_decision_ledger_path(tmp_path))
    assert [event.decision for event in events] == ["deferred", "accepted"]


def test_build_decision_queue_filters_phase(tmp_path):
    for phase, ticket_id in (("phase-10", "TKT-P10-001"), ("phase-11", "TKT-P11-001")):
        ticket_dir = tmp_path / ".agents" / "build-tickets" / phase
        ticket_dir.mkdir(parents=True)
        (ticket_dir / f"{ticket_id}-example.md").write_text("# Example", encoding="utf-8")
        record_decision(ticket_id, decision="accepted", reason="Ready.", root=tmp_path)

    decisions = build_decision_queue(tmp_path, phase="phase-11")

    assert [decision.ticket_id for decision in decisions] == ["TKT-P11-001"]


def test_current_decisions_from_events_uses_latest_sequence(tmp_path):
    record_decision("TKT-P11-001", decision="deferred", reason="Needs context.", root=tmp_path)
    record_decision("TKT-P11-001", decision="rejected", reason="Out of scope.", root=tmp_path)

    decisions = current_decisions_from_events(load_decision_events(default_decision_ledger_path(tmp_path)))

    assert len(decisions) == 1
    assert decisions[0].decision == "rejected"


def test_render_decision_queue_includes_counts_and_rows(tmp_path):
    record_decision("TKT-P11-001", decision="accepted", reason="Ready.", root=tmp_path)
    record_decision("TKT-P11-002", decision="rejected", reason="Out of scope.", root=tmp_path)

    rendered = render_decision_queue(build_decision_queue(tmp_path))

    assert "# Agent Ticket Decision Queue" in rendered
    assert "- Accepted: 1" in rendered
    assert "- Rejected: 1" in rendered
    assert "| TKT-P11-001 | accepted | - | Ready. |" in rendered


def test_render_decision_history_includes_events(tmp_path):
    record_decision("TKT-P11-001", decision="deferred", reason="Needs context.", root=tmp_path)
    record_decision("TKT-P11-001", decision="accepted", reason="Context added.", root=tmp_path)

    rendered = render_decision_history(load_decision_events(default_decision_ledger_path(tmp_path)))

    assert "# Agent Ticket Decision History" in rendered
    assert "- Events: 2" in rendered
    assert "| 1 | TKT-P11-001 | deferred | - | Needs context. |" in rendered
    assert "| 2 | TKT-P11-001 | accepted | - | Context added. |" in rendered


def test_render_decision_queue_handles_empty_queue():
    rendered = render_decision_queue(())

    assert "| none | none | none | none |" in rendered
