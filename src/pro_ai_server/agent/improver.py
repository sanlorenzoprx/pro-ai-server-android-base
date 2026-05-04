from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pro_ai_server.agent.reporter import AgentStatusSummary, build_ticket_status


@dataclass(frozen=True)
class MistakeRecord:
    path: Path
    title: str
    system_improvement: str
    prevent_next_time: str


@dataclass(frozen=True)
class ReportValidation:
    path: Path
    status: str
    details: tuple[str, ...]


@dataclass(frozen=True)
class SelfImprovementReview:
    status_summary: AgentStatusSummary
    mistakes: tuple[MistakeRecord, ...]
    validations: tuple[ReportValidation, ...]
    recommendations: tuple[str, ...]


def discover_mistake_records(root: Path = Path(".")) -> tuple[MistakeRecord, ...]:
    records: list[MistakeRecord] = []
    mistake_root = root / ".agents" / "mistakes"
    for path in sorted(mistake_root.glob("*.md")):
        if path.name.upper() == "README.MD":
            continue
        text = path.read_text(encoding="utf-8")
        records.append(
            MistakeRecord(
                path=path,
                title=_first_heading(text, fallback=path.stem),
                system_improvement=_one_line(_section_text(text, "System Improvement")) or "None recorded.",
                prevent_next_time=_one_line(_section_text(text, "Prevent Next Time")) or "None recorded.",
            )
        )
    return tuple(records)


def discover_report_validations(root: Path = Path(".")) -> tuple[ReportValidation, ...]:
    validations: list[ReportValidation] = []
    report_root = root / ".agents" / "reports"
    for path in sorted(report_root.glob("*.md")):
        if path.name.upper() in {"README.MD", "SELF-IMPROVEMENT-REVIEW.MD"}:
            continue
        text = path.read_text(encoding="utf-8")
        section = _section_text(text, "Validation Results") or _section_text(text, "Validation")
        if not section:
            validations.append(ReportValidation(path=path, status="missing", details=("No validation section found.",)))
            continue
        details = tuple(line.strip() for line in section.splitlines() if line.strip())
        normalized = section.lower()
        if "tbd" in normalized:
            status = "incomplete"
        elif "failed" in normalized or "error" in normalized:
            status = "needs-review"
        elif "passed" in normalized:
            status = "passed"
        else:
            status = "recorded"
        validations.append(ReportValidation(path=path, status=status, details=details))
    return tuple(validations)


def build_self_improvement_review(root: Path = Path("."), *, phase: str | None = None) -> SelfImprovementReview:
    status_summary = build_ticket_status(root, phase=phase)
    mistakes = discover_mistake_records(root)
    validations = discover_report_validations(root)
    recommendations = _build_recommendations(status_summary, mistakes, validations)
    return SelfImprovementReview(
        status_summary=status_summary,
        mistakes=mistakes,
        validations=validations,
        recommendations=tuple(recommendations),
    )


def render_self_improvement_review(review: SelfImprovementReview) -> str:
    lines = [
        "# Agent Self-Improvement Review",
        "",
        "## Ticket Status",
        "",
        f"- Planned: {review.status_summary.planned_count}",
        f"- Reported: {review.status_summary.reported_count}",
        f"- Orphan reports: {review.status_summary.orphan_report_count}",
        "",
        "## Validation Evidence",
        "",
        "| Report | Status |",
        "|---|---|",
    ]
    if not review.validations:
        lines.append("| none | missing |")
    for validation in review.validations:
        lines.append(f"| {_relative(validation.path)} | {validation.status} |")

    lines.extend(["", "## Mistake Records", ""])
    if not review.mistakes:
        lines.append("No mistake records found.")
    for mistake in review.mistakes:
        lines.extend(
            [
                f"### {mistake.title}",
                "",
                f"- File: `{_relative(mistake.path)}`",
                f"- System improvement: {mistake.system_improvement}",
                f"- Prevent next time: {mistake.prevent_next_time}",
                "",
            ]
        )

    lines.extend(["## Recommendations", ""])
    if not review.recommendations:
        lines.append("No improvements recommended.")
    for recommendation in review.recommendations:
        lines.append(f"- {recommendation}")
    lines.append("")
    return "\n".join(lines)


def write_self_improvement_review(
    review: SelfImprovementReview,
    *,
    root: Path = Path("."),
    output: Path | None = None,
) -> Path:
    path = output or root / ".agents" / "reports" / "self-improvement-review.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_self_improvement_review(review), encoding="utf-8")
    return path


def _build_recommendations(
    status_summary: AgentStatusSummary,
    mistakes: tuple[MistakeRecord, ...],
    validations: tuple[ReportValidation, ...],
) -> list[str]:
    recommendations: list[str] = []
    if status_summary.planned_count:
        recommendations.append("Write implementation reports for planned tickets before phase closeout.")
    if status_summary.orphan_report_count:
        recommendations.append("Reconcile orphan reports by adding missing ticket files or correcting ticket IDs.")
    if any(validation.status in {"missing", "incomplete", "needs-review"} for validation in validations):
        recommendations.append("Update reports with concrete validation evidence before marking tickets complete.")
    for mistake in mistakes:
        if mistake.prevent_next_time != "None recorded.":
            recommendations.append(mistake.prevent_next_time)
    return _dedupe(recommendations)


def _first_heading(text: str, *, fallback: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or fallback
    return fallback


def _section_text(text: str, heading: str) -> str:
    lines = text.splitlines()
    heading_prefix = f"## {heading}".lower()
    capture = False
    captured: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            if capture:
                break
            capture = stripped.lower() == heading_prefix
            continue
        if capture:
            captured.append(line)
    return "\n".join(captured).strip()


def _relative(path: Path) -> str:
    try:
        return path.relative_to(Path(".")).as_posix()
    except ValueError:
        return path.as_posix()


def _dedupe(items: list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    deduped: list[str] = []
    for item in items:
        normalized = item.strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            deduped.append(normalized)
    return tuple(deduped)


def _one_line(text: str) -> str:
    return " ".join(line.strip() for line in text.splitlines() if line.strip())
