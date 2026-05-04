from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from pro_ai_server.agent.reporter import extract_ticket_id


@dataclass(frozen=True)
class TicketDraft:
    ticket_id: str
    title: str
    recommendation: str
    path: Path
    text: str


def extract_recommendations(review_text: str) -> tuple[str, ...]:
    section = _section_text(review_text, "Recommendations")
    recommendations: list[str] = []
    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            recommendations.append(stripped[2:].strip())
    return tuple(item for item in recommendations if item)


def select_accepted_recommendations(
    available: tuple[str, ...],
    *,
    accepted: tuple[str, ...] = (),
    include_all: bool = False,
) -> tuple[str, ...]:
    if include_all:
        return available
    if not accepted:
        return ()

    selected: list[str] = []
    for accepted_item in accepted:
        normalized = accepted_item.strip().lower()
        for recommendation in available:
            candidate = recommendation.lower()
            if normalized == candidate or normalized in candidate:
                selected.append(recommendation)
                break
        else:
            selected.append(accepted_item.strip())
    return _dedupe(selected)


def build_ticket_drafts(
    recommendations: tuple[str, ...],
    *,
    root: Path = Path("."),
    phase: str = "phase-10",
    ticket_prefix: str = "TKT-P10",
    start: int = 1,
) -> tuple[TicketDraft, ...]:
    drafts: list[TicketDraft] = []
    for offset, recommendation in enumerate(recommendations):
        number = start + offset
        ticket_id = f"{ticket_prefix}-{number:03d}"
        title = _title_for_recommendation(recommendation)
        slug = _slugify(title)
        path = root / ".agents" / "build-tickets" / phase / f"{ticket_id}-{slug}.md"
        text = render_ticket_draft(ticket_id, title=title, recommendation=recommendation)
        drafts.append(TicketDraft(ticket_id=ticket_id, title=title, recommendation=recommendation, path=path, text=text))
    return tuple(drafts)


def next_ticket_number(root: Path = Path("."), *, phase: str = "phase-10", ticket_prefix: str = "TKT-P10") -> int:
    ticket_dir = root / ".agents" / "build-tickets" / phase
    numbers: list[int] = []
    prefix = f"{ticket_prefix.upper()}-"
    for path in ticket_dir.glob("*.md"):
        ticket_id = extract_ticket_id(path.name)
        if ticket_id and ticket_id.startswith(prefix):
            try:
                numbers.append(int(ticket_id.removeprefix(prefix)))
            except ValueError:
                continue
    return max(numbers, default=0) + 1


def render_ticket_draft(ticket_id: str, *, title: str, recommendation: str) -> str:
    return "\n".join(
        [
            f"# {ticket_id} {title}",
            "",
            "## Objective",
            "",
            recommendation,
            "",
            "## Source",
            "",
            "Self-improvement recommendation accepted for ticketization.",
            "",
            "## Acceptance Criteria",
            "",
            "- Recommendation is reviewed before implementation.",
            "- Implementation is scoped to this ticket.",
            "- Validation evidence is recorded in `.agents/reports/`.",
            "",
            "## Validation",
            "",
            "```powershell",
            "ruff check .",
            "pytest",
            "pro-ai-server validate-release",
            "```",
        ]
    )


def write_ticket_drafts(drafts: tuple[TicketDraft, ...], *, force: bool = False) -> tuple[Path, ...]:
    written: list[Path] = []
    for draft in drafts:
        if draft.path.exists() and not force:
            raise FileExistsError(f"Ticket already exists: {draft.path}")
        draft.path.parent.mkdir(parents=True, exist_ok=True)
        draft.path.write_text(draft.text, encoding="utf-8")
        written.append(draft.path)
    return tuple(written)


def render_ticketize_preview(drafts: tuple[TicketDraft, ...]) -> str:
    lines = ["# Ticketize Recommendations", ""]
    if not drafts:
        lines.append("No accepted recommendations selected.")
        return "\n".join(lines)
    lines.extend(["| Ticket | Path | Title |", "|---|---|---|"])
    for draft in drafts:
        lines.append(f"| {draft.ticket_id} | {draft.path.as_posix()} | {draft.title} |")
    return "\n".join(lines)


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


def _title_for_recommendation(recommendation: str) -> str:
    cleaned = recommendation.strip().rstrip(".")
    words = cleaned.split()
    title = " ".join(words[:8]) if words else "Self-Improvement Item"
    return title[0].upper() + title[1:] if title else "Self-Improvement Item"


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.strip().lower()).strip("-")
    return slug or "self-improvement-item"


def _dedupe(items: list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    deduped: list[str] = []
    for item in items:
        normalized = item.strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            deduped.append(normalized)
    return tuple(deduped)
