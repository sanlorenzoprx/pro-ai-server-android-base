from pro_ai_server.agent.reconciliation import build_session_report_reconciliation
from pro_ai_server.agent.reporter import build_implementation_report, write_implementation_report
from pro_ai_server.agent.session_archive import (
    apply_session_archive_plan,
    build_session_archive_plan,
    default_session_archive_path,
    render_session_archive_plan,
)
from pro_ai_server.agent.sessions import build_work_sessions, record_session_event


def test_session_archive_plan_selects_finished_reported_sessions(tmp_path):
    ticket_path = _write_ticket(tmp_path, "phase-19", "TKT-P19-001", "Archive")
    record_session_event("TKT-P19-001", event="finished", note="Done.", root=tmp_path)
    report = build_implementation_report("TKT-P19-001", summary="Done.", ticket_path=ticket_path)
    write_implementation_report("TKT-P19-001", report, root=tmp_path)

    plan = build_session_archive_plan(tmp_path, phase="phase-19")

    assert plan.archive_count == 1
    assert plan.items[0].ticket_id == "TKT-P19-001"
    assert plan.items[0].report_path == tmp_path / ".agents" / "reports" / "TKT-P19-001-report.md"


def test_session_archive_plan_ignores_finished_unreported_sessions(tmp_path):
    _write_ticket(tmp_path, "phase-19", "TKT-P19-001", "Archive")
    record_session_event("TKT-P19-001", event="finished", note="Done.", root=tmp_path)

    plan = build_session_archive_plan(tmp_path, phase="phase-19")

    assert plan.archive_count == 0


def test_apply_session_archive_plan_removes_current_state_but_preserves_archive_record(tmp_path):
    ticket_path = _write_ticket(tmp_path, "phase-19", "TKT-P19-001", "Archive")
    record_session_event("TKT-P19-001", event="finished", note="Done.", root=tmp_path)
    report = build_implementation_report("TKT-P19-001", summary="Done.", ticket_path=ticket_path)
    write_implementation_report("TKT-P19-001", report, root=tmp_path)

    result = apply_session_archive_plan(build_session_archive_plan(tmp_path, phase="phase-19"))

    archive = default_session_archive_path(tmp_path)
    assert result.write is True
    assert build_work_sessions(tmp_path, phase="phase-19") == ()
    assert "TKT-P19-001" in archive.read_text(encoding="utf-8")
    assert build_session_report_reconciliation(tmp_path, phase="phase-19").warning_count == 0


def test_session_archive_plan_filters_ticket_id(tmp_path):
    for ticket_id in ("TKT-P19-001", "TKT-P19-002"):
        ticket_path = _write_ticket(tmp_path, "phase-19", ticket_id, "Archive")
        record_session_event(ticket_id, event="finished", note="Done.", root=tmp_path)
        report = build_implementation_report(ticket_id, summary="Done.", ticket_path=ticket_path)
        write_implementation_report(ticket_id, report, root=tmp_path)

    plan = build_session_archive_plan(tmp_path, ticket_id="TKT-P19-002")

    assert [item.ticket_id for item in plan.items] == ["TKT-P19-002"]


def test_render_session_archive_plan_includes_mode_and_candidates(tmp_path):
    ticket_path = _write_ticket(tmp_path, "phase-19", "TKT-P19-001", "Archive")
    record_session_event("TKT-P19-001", event="finished", note="Done.", root=tmp_path)
    report = build_implementation_report("TKT-P19-001", summary="Done.", ticket_path=ticket_path)
    write_implementation_report("TKT-P19-001", report, root=tmp_path)

    rendered = render_session_archive_plan(build_session_archive_plan(tmp_path, phase="phase-19"))

    assert "# Agent Session Archive" in rendered
    assert "- Mode: preview" in rendered
    assert "- Archive candidates: 1" in rendered
    assert "TKT-P19-001" in rendered


def _write_ticket(tmp_path, phase, ticket_id, title):
    ticket_dir = tmp_path / ".agents" / "build-tickets" / phase
    ticket_dir.mkdir(parents=True, exist_ok=True)
    path = ticket_dir / f"{ticket_id}-{title.lower()}.md"
    path.write_text(f"# {ticket_id} {title}", encoding="utf-8")
    return path
