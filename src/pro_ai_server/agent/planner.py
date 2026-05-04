from __future__ import annotations

import re
from pathlib import Path


def slugify_feature(feature: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", feature.strip().lower()).strip("-")
    return slug or "plan"


def validate_plan_slug(slug: str) -> str:
    normalized = slug.strip().removesuffix(".plan.md").removesuffix(".md")
    if not normalized or "/" in normalized or "\\" in normalized:
        raise ValueError("Plan slug must be a filename-safe value without path separators.")
    return normalized


def plan_path_for_request(feature: str, *, root: Path = Path("."), slug: str | None = None) -> Path:
    plan_slug = validate_plan_slug(slug) if slug is not None else slugify_feature(feature)
    return root / ".agents" / "plans" / f"{plan_slug}.plan.md"


def build_plan_draft(
    feature: str,
    *,
    project_memory: str = "",
    prime_report: str = "",
    indexed_context: str = "",
) -> str:
    return "\n".join(
        [
            f"# Plan: {feature}",
            "",
            "> Draft only. Do not implement until this plan is reviewed and accepted.",
            "",
            "## Summary",
            "",
            f"Create an implementation plan for: {feature}",
            "",
            "## User Story",
            "",
            "As a Pro CodeFlow Server operator, I want this change planned before implementation so the work stays reviewable and validated.",
            "",
            "## Project Memory",
            "",
            project_memory.strip() or "No project memory found.",
            "",
            "## Prime Context",
            "",
            prime_report.strip() or "No prime report found. Run `pro-ai-server agent prime`.",
            "",
            "## Indexed Context",
            "",
            indexed_context.strip() or "No indexed context found. Run `pro-ai-server index .`.",
            "",
            "## Existing Patterns",
            "",
            "- Follow the current Typer CLI, dataclass, pytest, and report patterns.",
            "- Keep runtime changes small and ticket-scoped.",
            "",
            "## Files to Change",
            "",
            "| File | Action | Purpose |",
            "|---|---|---|",
            "| TBD | TBD | Confirm during plan review |",
            "",
            "## Relevant Files",
            "",
            "Review the indexed context above and replace this section with specific files before implementation.",
            "",
            "## Tasks",
            "",
            "### Task 1",
            "",
            "- File: TBD",
            "- Action: TBD",
            "- Details: TBD",
            "- Validate: `pytest` focused tests",
            "",
            "## Validation",
            "",
            "```bash",
            "ruff check .",
            "pytest",
            "pro-ai-server validate-release",
            "```",
            "",
            "## Acceptance Criteria",
            "",
            "- Plan is reviewed before implementation.",
            "- Tests are added or updated for changed behavior.",
            "- Validation evidence is recorded in `.agents/reports/`.",
            "",
            "## Rollback Plan",
            "",
            "Revert the ticket-scoped files changed during implementation.",
            "",
        ]
    )


def write_plan(plan: str, feature: str, *, root: Path = Path("."), slug: str | None = None) -> Path:
    path = plan_path_for_request(feature, root=root, slug=slug)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(plan, encoding="utf-8")
    return path
