from pro_ai_server.agent.execution import (
    build_execution_packet,
    default_execution_packet_path,
    render_execution_packet,
    render_next_action,
    select_next_action,
    write_execution_packet,
)
from pro_ai_server.agent.queue import record_decision
from pro_ai_server.agent.reporter import build_implementation_report, write_implementation_report
from pro_ai_server.agent.sessions import record_session_event


def test_select_next_action_picks_first_ready_accepted_ticket_by_stable_order(tmp_path):
    _write_ticket(tmp_path, "phase-14", "TKT-P14-002", "Second")
    _write_ticket(tmp_path, "phase-14", "TKT-P14-001", "First")
    record_decision("TKT-P14-002", decision="accepted", reason="Ready.", root=tmp_path)
    record_decision("TKT-P14-001", decision="accepted", reason="Ready.", root=tmp_path)

    selection = select_next_action(tmp_path, phase="phase-14")

    assert selection.has_ticket is True
    assert selection.item is not None
    assert selection.item.ticket_id == "TKT-P14-001"
    assert "phase-14/TKT-P14-001" in selection.reason


def test_select_next_action_ignores_reported_ticket(tmp_path):
    ticket_path = _write_ticket(tmp_path, "phase-14", "TKT-P14-001", "First")
    record_decision("TKT-P14-001", decision="accepted", reason="Ready.", root=tmp_path)
    report = build_implementation_report("TKT-P14-001", summary="Done.", ticket_path=ticket_path)
    write_implementation_report("TKT-P14-001", report, root=tmp_path)

    selection = select_next_action(tmp_path, phase="phase-14")

    assert selection.has_ticket is False
    assert "No accepted unreported tickets" in selection.reason


def test_select_next_action_skips_finished_session_by_default(tmp_path):
    _write_ticket(tmp_path, "phase-16", "TKT-P16-001", "Finished")
    _write_ticket(tmp_path, "phase-16", "TKT-P16-002", "Available")
    record_decision("TKT-P16-001", decision="accepted", reason="Ready.", root=tmp_path)
    record_decision("TKT-P16-002", decision="accepted", reason="Ready.", root=tmp_path)
    record_session_event("TKT-P16-001", event="finished", note="Done but not reported.", root=tmp_path)

    selection = select_next_action(tmp_path, phase="phase-16")

    assert selection.item is not None
    assert selection.item.ticket_id == "TKT-P16-002"
    assert "Skipped 1 finished" in selection.reason


def test_select_next_action_resume_policy_prioritizes_active_session(tmp_path):
    _write_ticket(tmp_path, "phase-16", "TKT-P16-001", "Available")
    _write_ticket(tmp_path, "phase-16", "TKT-P16-002", "Started")
    record_decision("TKT-P16-001", decision="accepted", reason="Ready.", root=tmp_path)
    record_decision("TKT-P16-002", decision="accepted", reason="Ready.", root=tmp_path)
    record_session_event("TKT-P16-002", event="started", note="Resume this.", root=tmp_path)

    selection = select_next_action(tmp_path, phase="phase-16", session_policy="resume")

    assert selection.item is not None
    assert selection.item.ticket_id == "TKT-P16-002"
    assert selection.session_status == "started"
    assert "Resume this." == selection.session_note


def test_select_next_action_all_policy_can_select_finished_session(tmp_path):
    _write_ticket(tmp_path, "phase-16", "TKT-P16-001", "Finished")
    record_decision("TKT-P16-001", decision="accepted", reason="Ready.", root=tmp_path)
    record_session_event("TKT-P16-001", event="finished", note="Needs report.", root=tmp_path)

    selection = select_next_action(tmp_path, phase="phase-16", session_policy="all")

    assert selection.item is not None
    assert selection.item.ticket_id == "TKT-P16-001"
    assert selection.session_status == "finished"


def test_render_next_action_handles_idle_state(tmp_path):
    rendered = render_next_action(select_next_action(tmp_path))

    assert "# Agent Next Action" in rendered
    assert "- Status: idle" in rendered


def test_render_next_action_includes_session_status(tmp_path):
    _write_ticket(tmp_path, "phase-16", "TKT-P16-001", "Started")
    record_decision("TKT-P16-001", decision="accepted", reason="Ready.", root=tmp_path)
    record_session_event("TKT-P16-001", event="started", note="Working.", root=tmp_path)

    rendered = render_next_action(select_next_action(tmp_path, phase="phase-16", session_policy="resume"))

    assert "- Session: started" in rendered


def test_render_execution_packet_includes_ticket_context_and_commands(tmp_path):
    _write_ticket(tmp_path, "phase-14", "TKT-P14-001", "Packet")
    record_decision("TKT-P14-001", decision="accepted", reason="Good next slice.", root=tmp_path)

    packet = build_execution_packet(tmp_path, phase="phase-14", indexed_context="# Project Context\nUse handoff.")
    rendered = render_execution_packet(packet)

    assert packet is not None
    assert "# Agent Execution Packet" in rendered
    assert "- Ticket: TKT-P14-001" in rendered
    assert "## Ticket Text" in rendered
    assert "Good next slice." in rendered
    assert "- Session: none" in rendered
    assert "Use handoff." in rendered
    assert "`ruff check .`" in rendered
    assert "pro-ai-server agent report TKT-P14-001" in rendered


def test_write_execution_packet_uses_default_path(tmp_path):
    _write_ticket(tmp_path, "phase-14", "TKT-P14-001", "Packet")
    record_decision("TKT-P14-001", decision="accepted", reason="Ready.", root=tmp_path)
    packet = build_execution_packet(tmp_path, phase="phase-14")

    assert packet is not None
    path = write_execution_packet(packet, root=tmp_path)

    assert path == default_execution_packet_path("TKT-P14-001", root=tmp_path)
    assert path.exists()
    assert "TKT-P14-001" in path.read_text(encoding="utf-8")


def _write_ticket(tmp_path, phase, ticket_id, title):
    ticket_dir = tmp_path / ".agents" / "build-tickets" / phase
    ticket_dir.mkdir(parents=True, exist_ok=True)
    path = ticket_dir / f"{ticket_id}-{title.lower()}.md"
    path.write_text(f"# {ticket_id} {title}\n\n## Objective\n\nDo it.", encoding="utf-8")
    return path
