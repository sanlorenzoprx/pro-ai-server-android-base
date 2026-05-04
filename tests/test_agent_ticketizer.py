import pytest

from pro_ai_server.agent.ticketizer import (
    build_ticket_drafts,
    extract_recommendations,
    next_ticket_number,
    render_ticketize_preview,
    select_accepted_recommendations,
    write_ticket_drafts,
)


def test_extract_recommendations_from_review_section():
    review = "\n".join(
        [
            "# Review",
            "",
            "## Recommendations",
            "",
            "- Add missing validation evidence.",
            "- Test optional inputs.",
            "",
            "## Other",
            "",
            "- ignored",
        ]
    )

    assert extract_recommendations(review) == ("Add missing validation evidence.", "Test optional inputs.")


def test_select_accepted_recommendations_matches_partial_text():
    available = ("Add missing validation evidence.", "Test optional inputs.")

    selected = select_accepted_recommendations(available, accepted=("validation",))

    assert selected == ("Add missing validation evidence.",)


def test_select_accepted_recommendations_can_include_all():
    available = ("Add missing validation evidence.", "Test optional inputs.")

    assert select_accepted_recommendations(available, include_all=True) == available


def test_build_ticket_drafts_uses_phase_prefix_and_stable_slug(tmp_path):
    drafts = build_ticket_drafts(
        ("Add missing validation evidence.",),
        root=tmp_path,
        phase="phase-10",
        ticket_prefix="TKT-P10",
        start=3,
    )

    assert len(drafts) == 1
    assert drafts[0].ticket_id == "TKT-P10-003"
    assert drafts[0].path == (
        tmp_path
        / ".agents"
        / "build-tickets"
        / "phase-10"
        / "TKT-P10-003-add-missing-validation-evidence.md"
    )
    assert "# TKT-P10-003 Add missing validation evidence" in drafts[0].text


def test_write_ticket_drafts_refuses_existing_file_without_force(tmp_path):
    drafts = build_ticket_drafts(("Add missing validation evidence.",), root=tmp_path)
    write_ticket_drafts(drafts)

    with pytest.raises(FileExistsError):
        write_ticket_drafts(drafts)


def test_write_ticket_drafts_overwrites_with_force(tmp_path):
    drafts = build_ticket_drafts(("Add missing validation evidence.",), root=tmp_path)
    write_ticket_drafts(drafts)

    paths = write_ticket_drafts(drafts, force=True)

    assert paths == (drafts[0].path,)
    assert "Validation evidence is recorded" in drafts[0].path.read_text(encoding="utf-8")


def test_next_ticket_number_uses_existing_phase_tickets(tmp_path):
    ticket_dir = tmp_path / ".agents" / "build-tickets" / "phase-10"
    ticket_dir.mkdir(parents=True)
    (ticket_dir / "TKT-P10-001-existing.md").write_text("# Existing", encoding="utf-8")
    (ticket_dir / "TKT-P10-005-existing.md").write_text("# Existing", encoding="utf-8")

    assert next_ticket_number(tmp_path, phase="phase-10", ticket_prefix="TKT-P10") == 6


def test_render_ticketize_preview_handles_empty_selection():
    assert "No accepted recommendations selected." in render_ticketize_preview(())
