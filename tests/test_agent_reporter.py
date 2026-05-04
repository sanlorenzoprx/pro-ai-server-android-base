import pytest

from pro_ai_server.agent.reporter import (
    build_implementation_report,
    build_ticket_status,
    discover_reports,
    discover_tickets,
    extract_ticket_id,
    report_path_for_ticket,
    render_ticket_status,
    validate_report_slug,
    write_implementation_report,
)


def test_extract_ticket_id_from_filename_and_text():
    assert extract_ticket_id("TKT-P8-001-ticket-status.md") == "TKT-P8-001"
    assert extract_ticket_id("# tkt-p8-002 implementation") == "TKT-P8-002"
    assert extract_ticket_id("no ticket") is None


def test_report_path_for_ticket_is_stable(tmp_path):
    assert report_path_for_ticket("TKT-P8-001", root=tmp_path) == (
        tmp_path / ".agents" / "reports" / "TKT-P8-001-report.md"
    )
    assert report_path_for_ticket("TKT-P8-001", root=tmp_path, slug="ticket-status.md") == (
        tmp_path / ".agents" / "reports" / "ticket-status-report.md"
    )


def test_validate_report_slug_rejects_path_separators():
    with pytest.raises(ValueError, match="filename-safe"):
        validate_report_slug("../bad")


def test_discover_tickets_reads_phase_and_title(tmp_path):
    ticket_dir = tmp_path / ".agents" / "build-tickets" / "phase-8"
    ticket_dir.mkdir(parents=True)
    (ticket_dir / "TKT-P8-001-ticket-status.md").write_text("# Ticket Status\n\nDetails", encoding="utf-8")

    tickets = discover_tickets(tmp_path)

    assert len(tickets) == 1
    assert tickets[0].ticket_id == "TKT-P8-001"
    assert tickets[0].title == "Ticket Status"
    assert tickets[0].phase == "phase-8"


def test_status_marks_ticket_reported_when_matching_report_exists(tmp_path):
    ticket_dir = tmp_path / ".agents" / "build-tickets" / "phase-8"
    ticket_dir.mkdir(parents=True)
    (ticket_dir / "TKT-P8-001-ticket-status.md").write_text("# Ticket Status", encoding="utf-8")
    write_implementation_report("TKT-P8-001", "# TKT-P8-001 Implementation Report", root=tmp_path)

    summary = build_ticket_status(tmp_path)

    assert summary.reported_count == 1
    assert summary.planned_count == 0
    assert summary.statuses[0].status == "reported"


def test_status_marks_ticket_planned_without_report(tmp_path):
    ticket_dir = tmp_path / ".agents" / "build-tickets" / "phase-8"
    ticket_dir.mkdir(parents=True)
    (ticket_dir / "TKT-P8-001-ticket-status.md").write_text("# Ticket Status", encoding="utf-8")

    summary = build_ticket_status(tmp_path)

    assert summary.planned_count == 1
    assert summary.statuses[0].status == "planned"


def test_status_detects_orphan_report(tmp_path):
    write_implementation_report("TKT-P8-999", "# TKT-P8-999 Implementation Report", root=tmp_path)

    summary = build_ticket_status(tmp_path)

    assert summary.orphan_report_count == 1
    assert summary.statuses[0].status == "orphan-report"


def test_phase_filter_limits_ticket_statuses(tmp_path):
    for phase, ticket_id in (("phase-7", "TKT-P7-001"), ("phase-8", "TKT-P8-001")):
        ticket_dir = tmp_path / ".agents" / "build-tickets" / phase
        ticket_dir.mkdir(parents=True)
        (ticket_dir / f"{ticket_id}-ticket.md").write_text(f"# {ticket_id}", encoding="utf-8")

    summary = build_ticket_status(tmp_path, phase="phase-8")

    assert [status.ticket_id for status in summary.statuses] == ["TKT-P8-001"]


def test_build_report_draft_is_deterministic():
    report = build_implementation_report(
        "TKT-P8-001",
        summary="Implemented status scanner.",
        files_created=("src/pro_ai_server/agent/reporter.py",),
        files_updated=("src/pro_ai_server/cli.py",),
        validation=("pytest tests/test_agent_reporter.py",),
    )

    assert "# TKT-P8-001 Implementation Report" in report
    assert "Implemented status scanner." in report
    assert "- src/pro_ai_server/agent/reporter.py" in report
    assert "- pytest tests/test_agent_reporter.py" in report


def test_discover_reports_reads_ticket_id_from_body(tmp_path):
    report_dir = tmp_path / ".agents" / "reports"
    report_dir.mkdir(parents=True)
    (report_dir / "phase-8-closeout-report.md").write_text("Completed: TKT-P8-001", encoding="utf-8")

    reports = discover_reports(tmp_path)

    assert len(reports) == 1
    assert reports[0].ticket_id == "TKT-P8-001"


def test_render_ticket_status_includes_counts(tmp_path):
    ticket_dir = tmp_path / ".agents" / "build-tickets" / "phase-8"
    ticket_dir.mkdir(parents=True)
    (ticket_dir / "TKT-P8-001-ticket-status.md").write_text("# Ticket Status", encoding="utf-8")

    rendered = render_ticket_status(build_ticket_status(tmp_path))

    assert "# Agent Ticket Status" in rendered
    assert "- Planned: 1" in rendered
    assert "| TKT-P8-001 | planned | phase-8 | - |" in rendered
