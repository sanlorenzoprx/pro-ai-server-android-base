from pro_ai_server.agent.handoff import build_handoff_view, render_handoff_view
from pro_ai_server.agent.queue import record_decision
from pro_ai_server.agent.reporter import build_implementation_report, write_implementation_report


def test_handoff_view_includes_accepted_unreported_ticket(tmp_path):
    ticket_dir = tmp_path / ".agents" / "build-tickets" / "phase-13"
    ticket_dir.mkdir(parents=True)
    (ticket_dir / "TKT-P13-001-handoff.md").write_text("# TKT-P13-001 Handoff\n\n## Objective\n\nDo it.", encoding="utf-8")
    record_decision("TKT-P13-001", decision="accepted", reason="Ready.", root=tmp_path)

    view = build_handoff_view(tmp_path, phase="phase-13")

    assert len(view.items) == 1
    assert view.ready_count == 1
    assert view.items[0].ticket_id == "TKT-P13-001"
    assert view.items[0].title == "Handoff"


def test_handoff_view_excludes_reported_ticket_by_default(tmp_path):
    ticket_dir = tmp_path / ".agents" / "build-tickets" / "phase-13"
    ticket_dir.mkdir(parents=True)
    ticket_path = ticket_dir / "TKT-P13-001-handoff.md"
    ticket_path.write_text("# TKT-P13-001 Handoff", encoding="utf-8")
    record_decision("TKT-P13-001", decision="accepted", reason="Ready.", root=tmp_path)
    report = build_implementation_report("TKT-P13-001", summary="Done.", ticket_path=ticket_path)
    write_implementation_report("TKT-P13-001", report, root=tmp_path)

    view = build_handoff_view(tmp_path, phase="phase-13")

    assert view.items == ()


def test_handoff_view_can_include_reported_ticket(tmp_path):
    ticket_dir = tmp_path / ".agents" / "build-tickets" / "phase-13"
    ticket_dir.mkdir(parents=True)
    ticket_path = ticket_dir / "TKT-P13-001-handoff.md"
    ticket_path.write_text("# TKT-P13-001 Handoff", encoding="utf-8")
    record_decision("TKT-P13-001", decision="accepted", reason="Ready.", root=tmp_path)
    report = build_implementation_report("TKT-P13-001", summary="Done.", ticket_path=ticket_path)
    write_implementation_report("TKT-P13-001", report, root=tmp_path)

    view = build_handoff_view(tmp_path, phase="phase-13", include_reported=True)

    assert view.reported_count == 1
    assert view.items[0].implementation_status == "reported"


def test_handoff_view_filters_ticket_id(tmp_path):
    ticket_dir = tmp_path / ".agents" / "build-tickets" / "phase-13"
    ticket_dir.mkdir(parents=True)
    for ticket_id in ("TKT-P13-001", "TKT-P13-002"):
        (ticket_dir / f"{ticket_id}-handoff.md").write_text(f"# {ticket_id} Handoff", encoding="utf-8")
        record_decision(ticket_id, decision="accepted", reason="Ready.", root=tmp_path)

    view = build_handoff_view(tmp_path, phase="phase-13", ticket_id="TKT-P13-002")

    assert [item.ticket_id for item in view.items] == ["TKT-P13-002"]


def test_render_handoff_view_includes_next_steps(tmp_path):
    ticket_dir = tmp_path / ".agents" / "build-tickets" / "phase-13"
    ticket_dir.mkdir(parents=True)
    (ticket_dir / "TKT-P13-001-handoff.md").write_text("# TKT-P13-001 Handoff", encoding="utf-8")
    record_decision("TKT-P13-001", decision="accepted", reason="Ready.", root=tmp_path)

    rendered = render_handoff_view(build_handoff_view(tmp_path, phase="phase-13"))

    assert "# Agent Implementation Handoff" in rendered
    assert "- Ready: 1" in rendered
    assert "## 1. TKT-P13-001 Handoff" in rendered
    assert "pro-ai-server agent report" in rendered


def test_render_handoff_view_handles_empty_view(tmp_path):
    assert "No accepted tickets need implementation." in render_handoff_view(build_handoff_view(tmp_path))
