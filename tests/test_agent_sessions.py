from pro_ai_server.agent.execution import default_execution_packet_path
from pro_ai_server.agent.sessions import (
    build_work_sessions,
    current_sessions_from_events,
    default_session_ledger_path,
    default_session_path,
    load_session_events,
    record_session_event,
    render_session_history,
    render_work_sessions,
    validate_session_event,
)


def test_validate_session_event_accepts_aliases():
    assert validate_session_event("pickup") == "picked-up"
    assert validate_session_event("start") == "started"
    assert validate_session_event("finish") == "finished"


def test_record_session_event_writes_current_state_and_ledger(tmp_path):
    _write_ticket(tmp_path, "phase-15", "TKT-P15-001", "Session")
    packet = default_execution_packet_path("TKT-P15-001", root=tmp_path)
    packet.parent.mkdir(parents=True)
    packet.write_text("# Agent Execution Packet", encoding="utf-8")

    session = record_session_event("TKT-P15-001", event="pickup", note="Taking it.", root=tmp_path)

    assert session.ticket_id == "TKT-P15-001"
    assert session.status == "picked-up"
    assert session.phase == "phase-15"
    assert session.packet_path == packet
    assert default_session_path(tmp_path).exists()
    assert default_session_ledger_path(tmp_path).exists()


def test_current_sessions_from_events_keeps_latest_event(tmp_path):
    _write_ticket(tmp_path, "phase-15", "TKT-P15-001", "Session")
    record_session_event("TKT-P15-001", event="picked-up", note="Taking it.", root=tmp_path)
    record_session_event("TKT-P15-001", event="started", note="Working.", root=tmp_path)

    sessions = current_sessions_from_events(load_session_events(default_session_ledger_path(tmp_path)))

    assert len(sessions) == 1
    assert sessions[0].status == "started"
    assert sessions[0].note == "Working."


def test_build_work_sessions_filters_phase_and_ticket(tmp_path):
    _write_ticket(tmp_path, "phase-15", "TKT-P15-001", "Session")
    _write_ticket(tmp_path, "phase-16", "TKT-P16-001", "Later")
    record_session_event("TKT-P15-001", event="picked-up", root=tmp_path)
    record_session_event("TKT-P16-001", event="picked-up", root=tmp_path)

    phase_sessions = build_work_sessions(tmp_path, phase="phase-15")
    ticket_sessions = build_work_sessions(tmp_path, ticket_id="TKT-P16-001")

    assert [session.ticket_id for session in phase_sessions] == ["TKT-P15-001"]
    assert [session.ticket_id for session in ticket_sessions] == ["TKT-P16-001"]


def test_render_work_sessions_includes_counts_and_note(tmp_path):
    _write_ticket(tmp_path, "phase-15", "TKT-P15-001", "Session")
    record_session_event("TKT-P15-001", event="finished", note="Done.", root=tmp_path)

    rendered = render_work_sessions(build_work_sessions(tmp_path))

    assert "# Agent Work Sessions" in rendered
    assert "- Finished: 1" in rendered
    assert "| TKT-P15-001 | finished | phase-15 | - | Done. |" in rendered


def test_render_session_history_includes_events(tmp_path):
    _write_ticket(tmp_path, "phase-15", "TKT-P15-001", "Session")
    record_session_event("TKT-P15-001", event="picked-up", note="Taking it.", root=tmp_path)

    rendered = render_session_history(load_session_events(default_session_ledger_path(tmp_path)))

    assert "# Agent Work Session History" in rendered
    assert "- Events: 1" in rendered
    assert "TKT-P15-001" in rendered


def _write_ticket(tmp_path, phase, ticket_id, title):
    ticket_dir = tmp_path / ".agents" / "build-tickets" / phase
    ticket_dir.mkdir(parents=True, exist_ok=True)
    path = ticket_dir / f"{ticket_id}-{title.lower()}.md"
    path.write_text(f"# {ticket_id} {title}", encoding="utf-8")
    return path
