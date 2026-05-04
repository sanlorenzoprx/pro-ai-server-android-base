import pytest

from pro_ai_server.agent.planner import (
    build_plan_draft,
    plan_path_for_request,
    slugify_feature,
    validate_plan_slug,
    write_plan,
)


def test_slugify_feature_is_stable():
    assert slugify_feature("Add Route-Test Endpoint!") == "add-route-test-endpoint"
    assert slugify_feature("   ") == "plan"


def test_plan_path_for_request_uses_agents_plans(tmp_path):
    assert plan_path_for_request("Add Gateway", root=tmp_path) == tmp_path / ".agents" / "plans" / "add-gateway.plan.md"


def test_plan_path_for_request_accepts_explicit_slug(tmp_path):
    assert (
        plan_path_for_request("Add Gateway", root=tmp_path, slug="gateway-retry")
        == tmp_path / ".agents" / "plans" / "gateway-retry.plan.md"
    )


def test_validate_plan_slug_rejects_path_separators():
    with pytest.raises(ValueError, match="filename-safe"):
        validate_plan_slug("../bad")


def test_build_plan_draft_includes_context_sections():
    plan = build_plan_draft(
        "add gateway route",
        project_memory="Memory",
        prime_report="Prime",
        indexed_context="Context",
    )

    assert "# Plan: add gateway route" in plan
    assert "Memory" in plan
    assert "Prime" in plan
    assert "Context" in plan
    assert "## Relevant Files" in plan
    assert "Do not implement until this plan is reviewed" in plan


def test_write_plan_creates_file(tmp_path):
    path = write_plan("plan text", "Add Gateway", root=tmp_path)

    assert path == tmp_path / ".agents" / "plans" / "add-gateway.plan.md"
    assert path.read_text(encoding="utf-8") == "plan text"


def test_write_plan_accepts_explicit_slug(tmp_path):
    path = write_plan("plan text", "Add Gateway", root=tmp_path, slug="gateway-retry.md")

    assert path == tmp_path / ".agents" / "plans" / "gateway-retry.plan.md"
