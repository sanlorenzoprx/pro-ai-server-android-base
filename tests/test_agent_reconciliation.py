from pro_ai_server.agent.reconciliation import (
    build_session_report_reconciliation,
    render_session_report_reconciliation,
)
from pro_ai_server.agent.reporter import build_implementation_report, write_implementation_report
from pro_ai_server.agent.sessions import record_session_event


def test_reconciliation_warns_for_active_session_with_report(tmp_path):
    ticket_path = _write_ticket(tmp_path, "phase-17", "TKT-P17-001", "Active")
    record_session_event("TKT-P17-001", event="started", note="Working.", root=tmp_path)
    report = build_implementation_report("TKT-P17-001", summary="Done.", ticket_path=ticket_path)
    write_implementation_report("TKT-P17-001", report, root=tmp_path)

    reconciliation = build_session_report_reconciliation(tmp_path, phase="phase-17")

    assert [warning.code for warning in reconciliation.warnings] == ["active-session-reported"]
    assert reconciliation.warnings[0].session_status == "started"


def test_reconciliation_warns_for_finished_session_with_report(tmp_path):
    ticket_path = _write_ticket(tmp_path, "phase-17", "TKT-P17-001", "Finished")
    record_session_event("TKT-P17-001", event="finished", note="Done.", root=tmp_path)
    report = build_implementation_report("TKT-P17-001", summary="Done.", ticket_path=ticket_path)
    write_implementation_report("TKT-P17-001", report, root=tmp_path)

    reconciliation = build_session_report_reconciliation(tmp_path, phase="phase-17")

    assert [warning.code for warning in reconciliation.warnings] == ["finished-session-reported"]


def test_reconciliation_warns_for_finished_session_without_report(tmp_path):
    _write_ticket(tmp_path, "phase-17", "TKT-P17-001", "Finished")
    record_session_event("TKT-P17-001", event="finished", note="Done.", root=tmp_path)

    reconciliation = build_session_report_reconciliation(tmp_path, phase="phase-17")

    assert [warning.code for warning in reconciliation.warnings] == ["finished-session-unreported"]


def test_reconciliation_warns_for_orphan_session(tmp_path):
    record_session_event("TKT-P17-999", event="started", note="Missing ticket.", root=tmp_path)

    reconciliation = build_session_report_reconciliation(tmp_path)

    assert [warning.code for warning in reconciliation.warnings] == ["orphan-session"]


def test_reconciliation_filters_by_ticket(tmp_path):
    _write_ticket(tmp_path, "phase-17", "TKT-P17-001", "Finished")
    _write_ticket(tmp_path, "phase-17", "TKT-P17-002", "Finished")
    record_session_event("TKT-P17-001", event="finished", note="Done.", root=tmp_path)
    record_session_event("TKT-P17-002", event="finished", note="Done.", root=tmp_path)

    reconciliation = build_session_report_reconciliation(tmp_path, ticket_id="TKT-P17-002")

    assert [warning.ticket_id for warning in reconciliation.warnings] == ["TKT-P17-002"]


def test_render_reconciliation_includes_warning_summary(tmp_path):
    _write_ticket(tmp_path, "phase-17", "TKT-P17-001", "Finished")
    record_session_event("TKT-P17-001", event="finished", note="Done.", root=tmp_path)

    rendered = render_session_report_reconciliation(build_session_report_reconciliation(tmp_path))

    assert "# Agent Session Report Reconciliation" in rendered
    assert "- Warnings: 1" in rendered
    assert "finished-session-unreported" in rendered


def test_render_reconciliation_handles_clean_state(tmp_path):
    rendered = render_session_report_reconciliation(build_session_report_reconciliation(tmp_path))

    assert "- Warnings: 0" in rendered
    assert "| none | none | none | none | none | none | none |" in rendered


def _write_ticket(tmp_path, phase, ticket_id, title):
    ticket_dir = tmp_path / ".agents" / "build-tickets" / phase
    ticket_dir.mkdir(parents=True, exist_ok=True)
    path = ticket_dir / f"{ticket_id}-{title.lower()}.md"
    path.write_text(f"# {ticket_id} {title}", encoding="utf-8")
    return path
