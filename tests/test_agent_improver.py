from pro_ai_server.agent.improver import (
    build_self_improvement_review,
    discover_mistake_records,
    discover_report_validations,
    render_self_improvement_review,
    write_self_improvement_review,
)


def test_discover_mistake_records_extracts_improvement_sections(tmp_path):
    mistake_dir = tmp_path / ".agents" / "mistakes"
    mistake_dir.mkdir(parents=True)
    (mistake_dir / "2026-05-03-example.md").write_text(
        "\n".join(
            [
                "# Mistake: Example",
                "",
                "## System Improvement",
                "",
                "Add missing-input tests.",
                "",
                "## Prevent Next Time",
                "",
                "Test optional local inputs before closeout.",
            ]
        ),
        encoding="utf-8",
    )

    records = discover_mistake_records(tmp_path)

    assert len(records) == 1
    assert records[0].title == "Mistake: Example"
    assert records[0].system_improvement == "Add missing-input tests."
    assert records[0].prevent_next_time == "Test optional local inputs before closeout."


def test_discover_report_validations_marks_missing_incomplete_and_passed(tmp_path):
    report_dir = tmp_path / ".agents" / "reports"
    report_dir.mkdir(parents=True)
    (report_dir / "README.md").write_text("# Reports", encoding="utf-8")
    (report_dir / "self-improvement-review.md").write_text("# Agent Self-Improvement Review", encoding="utf-8")
    (report_dir / "missing.md").write_text("# Missing", encoding="utf-8")
    (report_dir / "incomplete.md").write_text("## Validation Results\n\nTBD", encoding="utf-8")
    (report_dir / "passed.md").write_text("## Validation\n\n- pytest: passed", encoding="utf-8")

    validations = discover_report_validations(tmp_path)

    assert [validation.status for validation in validations] == ["incomplete", "missing", "passed"]


def test_build_review_recommends_reports_validation_and_mistake_prevention(tmp_path):
    ticket_dir = tmp_path / ".agents" / "build-tickets" / "phase-9"
    ticket_dir.mkdir(parents=True)
    (ticket_dir / "TKT-P9-001-improve.md").write_text("# Improve", encoding="utf-8")
    mistake_dir = tmp_path / ".agents" / "mistakes"
    mistake_dir.mkdir(parents=True)
    (mistake_dir / "2026-05-03-example.md").write_text(
        "## Prevent Next Time\n\nAdd missing-input tests.",
        encoding="utf-8",
    )
    report_dir = tmp_path / ".agents" / "reports"
    report_dir.mkdir(parents=True)
    (report_dir / "TKT-P9-001-report.md").write_text("## Validation Results\n\nTBD", encoding="utf-8")

    review = build_self_improvement_review(tmp_path, phase="phase-9")

    assert review.status_summary.reported_count == 1
    assert "Update reports with concrete validation evidence before marking tickets complete." in review.recommendations
    assert "Add missing-input tests." in review.recommendations


def test_render_review_includes_status_validation_and_recommendations(tmp_path):
    ticket_dir = tmp_path / ".agents" / "build-tickets" / "phase-9"
    ticket_dir.mkdir(parents=True)
    (ticket_dir / "TKT-P9-001-improve.md").write_text("# Improve", encoding="utf-8")

    rendered = render_self_improvement_review(build_self_improvement_review(tmp_path, phase="phase-9"))

    assert "# Agent Self-Improvement Review" in rendered
    assert "- Planned: 1" in rendered
    assert "Write implementation reports for planned tickets before phase closeout." in rendered


def test_write_self_improvement_review_creates_default_report(tmp_path):
    review = build_self_improvement_review(tmp_path)

    path = write_self_improvement_review(review, root=tmp_path)

    assert path == tmp_path / ".agents" / "reports" / "self-improvement-review.md"
    assert "# Agent Self-Improvement Review" in path.read_text(encoding="utf-8")
