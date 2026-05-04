from pro_ai_server.agent.autopilot import render_autopilot_result, run_autopilot_once
from pro_ai_server.agent.queue import record_decision
from pro_ai_server.agent.sessions import build_work_sessions, record_session_event


def test_autopilot_preview_selects_next_ticket_without_writes(tmp_path):
    _write_ticket(tmp_path, "phase-18", "TKT-P18-001", "Autopilot")
    record_decision("TKT-P18-001", decision="accepted", reason="Ready.", root=tmp_path)

    result = run_autopilot_once(tmp_path, phase="phase-18")

    assert result.mode == "preview"
    assert result.status == "ready"
    assert result.ticket_id == "TKT-P18-001"
    assert result.packet_path is None
    assert not (tmp_path / ".agents" / "execution" / "TKT-P18-001.execution.md").exists()


def test_autopilot_execute_writes_packet_and_session_events(tmp_path):
    _write_ticket(tmp_path, "phase-18", "TKT-P18-001", "Autopilot")
    record_decision("TKT-P18-001", decision="accepted", reason="Ready.", root=tmp_path)

    result = run_autopilot_once(tmp_path, phase="phase-18", execute=True, start_session=True)

    packet = tmp_path / ".agents" / "execution" / "TKT-P18-001.execution.md"
    sessions = build_work_sessions(tmp_path, ticket_id="TKT-P18-001")
    assert result.status == "stopped"
    assert result.packet_path == packet
    assert packet.exists()
    assert result.session_events == ("picked-up", "started")
    assert sessions[0].status == "started"


def test_autopilot_stops_on_reconciliation_warnings(tmp_path):
    _write_ticket(tmp_path, "phase-18", "TKT-P18-001", "Autopilot")
    record_decision("TKT-P18-001", decision="accepted", reason="Ready.", root=tmp_path)
    record_session_event("TKT-P18-001", event="finished", note="Needs report.", root=tmp_path)

    result = run_autopilot_once(tmp_path, phase="phase-18")

    assert result.status == "stopped"
    assert result.reconciliation_warnings == 1
    assert "Reconciliation warnings" in result.stop_reason


def test_autopilot_stops_on_active_session_by_default(tmp_path):
    _write_ticket(tmp_path, "phase-18", "TKT-P18-001", "Autopilot")
    _write_ticket(tmp_path, "phase-18", "TKT-P18-002", "Next")
    record_decision("TKT-P18-001", decision="accepted", reason="Ready.", root=tmp_path)
    record_decision("TKT-P18-002", decision="accepted", reason="Ready.", root=tmp_path)
    record_session_event("TKT-P18-001", event="started", note="Working.", root=tmp_path)

    result = run_autopilot_once(tmp_path, phase="phase-18")

    assert result.status == "stopped"
    assert result.ticket_id is None
    assert "Active work session" in result.stop_reason


def test_autopilot_resume_policy_allows_active_session(tmp_path):
    _write_ticket(tmp_path, "phase-18", "TKT-P18-001", "Autopilot")
    _write_ticket(tmp_path, "phase-18", "TKT-P18-002", "Next")
    record_decision("TKT-P18-001", decision="accepted", reason="Ready.", root=tmp_path)
    record_decision("TKT-P18-002", decision="accepted", reason="Ready.", root=tmp_path)
    record_session_event("TKT-P18-001", event="started", note="Working.", root=tmp_path)

    result = run_autopilot_once(tmp_path, phase="phase-18", session_policy="resume")

    assert result.status == "ready"
    assert result.ticket_id == "TKT-P18-001"


def test_autopilot_stops_when_no_ready_ticket(tmp_path):
    result = run_autopilot_once(tmp_path, phase="phase-18")

    assert result.status == "stopped"
    assert result.ticket_id is None
    assert "No accepted unreported tickets" in result.stop_reason


def test_render_autopilot_result_includes_gates(tmp_path):
    _write_ticket(tmp_path, "phase-18", "TKT-P18-001", "Autopilot")
    record_decision("TKT-P18-001", decision="accepted", reason="Ready.", root=tmp_path)

    rendered = render_autopilot_result(run_autopilot_once(tmp_path, phase="phase-18"))

    assert "# Agent Autopilot" in rendered
    assert "- Ticket: TKT-P18-001" in rendered
    assert "## Validation Gate" in rendered
    assert "pro-ai-server agent report TKT-P18-001" in rendered


def _write_ticket(tmp_path, phase, ticket_id, title):
    ticket_dir = tmp_path / ".agents" / "build-tickets" / phase
    ticket_dir.mkdir(parents=True, exist_ok=True)
    path = ticket_dir / f"{ticket_id}-{title.lower()}.md"
    path.write_text(f"# {ticket_id} {title}", encoding="utf-8")
    return path
