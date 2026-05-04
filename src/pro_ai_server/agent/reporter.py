from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

TICKET_ID_PATTERN = re.compile(r"\bTKT-P\d+-\d+\b", re.IGNORECASE)


@dataclass(frozen=True)
class AgentTicket:
    ticket_id: str
    title: str
    path: Path
    phase: str


@dataclass(frozen=True)
class AgentReport:
    ticket_id: str
    path: Path


@dataclass(frozen=True)
class AgentTicketStatus:
    ticket_id: str
    status: str
    ticket_path: Path | None = None
    report_path: Path | None = None
    phase: str | None = None


@dataclass(frozen=True)
class AgentStatusSummary:
    statuses: tuple[AgentTicketStatus, ...]

    @property
    def planned_count(self) -> int:
        return sum(1 for status in self.statuses if status.status == "planned")

    @property
    def reported_count(self) -> int:
        return sum(1 for status in self.statuses if status.status == "reported")

    @property
    def orphan_report_count(self) -> int:
        return sum(1 for status in self.statuses if status.status == "orphan-report")


def extract_ticket_id(text: str) -> str | None:
    match = TICKET_ID_PATTERN.search(text)
    return match.group(0).upper() if match else None


def validate_report_slug(slug: str) -> str:
    normalized = slug.strip().removesuffix("-report").removesuffix(".md")
    if not normalized or "/" in normalized or "\\" in normalized:
        raise ValueError("Report slug must be a filename-safe value without path separators.")
    return normalized


def report_path_for_ticket(ticket_id: str, *, root: Path = Path("."), slug: str | None = None) -> Path:
    report_slug = validate_report_slug(slug) if slug is not None else ticket_id.upper()
    return root / ".agents" / "reports" / f"{report_slug}-report.md"


def discover_tickets(root: Path = Path(".")) -> tuple[AgentTicket, ...]:
    tickets: list[AgentTicket] = []
    ticket_root = root / ".agents" / "build-tickets"
    for path in sorted(ticket_root.glob("**/*.md")):
        ticket_id = extract_ticket_id(path.name)
        if not ticket_id:
            continue
        text = path.read_text(encoding="utf-8")
        title = _extract_title(text, fallback=path.stem)
        phase = path.parent.name if path.parent != ticket_root else ""
        tickets.append(AgentTicket(ticket_id=ticket_id, title=title, path=path, phase=phase))
    return tuple(tickets)


def discover_reports(root: Path = Path(".")) -> tuple[AgentReport, ...]:
    reports: list[AgentReport] = []
    report_root = root / ".agents" / "reports"
    for path in sorted(report_root.glob("*.md")):
        ticket_id = extract_ticket_id(path.name)
        if ticket_id is None:
            ticket_id = extract_ticket_id(path.read_text(encoding="utf-8"))
        if ticket_id:
            reports.append(AgentReport(ticket_id=ticket_id, path=path))
    return tuple(reports)


def build_ticket_status(root: Path = Path("."), *, phase: str | None = None) -> AgentStatusSummary:
    tickets = discover_tickets(root)
    reports = discover_reports(root)
    reports_by_ticket = {report.ticket_id: report for report in reports}
    ticket_ids = {ticket.ticket_id for ticket in tickets}

    statuses: list[AgentTicketStatus] = []
    for ticket in tickets:
        if phase and ticket.phase != phase:
            continue
        report = reports_by_ticket.get(ticket.ticket_id)
        statuses.append(
            AgentTicketStatus(
                ticket_id=ticket.ticket_id,
                status="reported" if report else "planned",
                ticket_path=ticket.path,
                report_path=report.path if report else None,
                phase=ticket.phase,
            )
        )

    if phase is None:
        for report in reports:
            if report.ticket_id not in ticket_ids:
                statuses.append(
                    AgentTicketStatus(
                        ticket_id=report.ticket_id,
                        status="orphan-report",
                        report_path=report.path,
                    )
                )

    statuses.sort(key=lambda status: (status.phase or "", status.ticket_id, status.status))
    return AgentStatusSummary(statuses=tuple(statuses))


def render_ticket_status(summary: AgentStatusSummary) -> str:
    lines = [
        "# Agent Ticket Status",
        "",
        f"- Planned: {summary.planned_count}",
        f"- Reported: {summary.reported_count}",
        f"- Orphan reports: {summary.orphan_report_count}",
        "",
        "| Ticket | Status | Phase | Report |",
        "|---|---|---|---|",
    ]
    if not summary.statuses:
        lines.append("| none | none | none | none |")
    for status in summary.statuses:
        report = _relative_or_none(status.report_path)
        lines.append(f"| {status.ticket_id} | {status.status} | {status.phase or '-'} | {report} |")
    return "\n".join(lines)


def build_implementation_report(
    ticket_id: str,
    *,
    summary: str,
    ticket_path: Path | None = None,
    files_created: tuple[str, ...] = (),
    files_updated: tuple[str, ...] = (),
    validation: tuple[str, ...] = (),
    deviations: tuple[str, ...] = (),
    follow_up: tuple[str, ...] = (),
) -> str:
    normalized_ticket_id = ticket_id.upper()
    return "\n".join(
        [
            f"# {normalized_ticket_id} Implementation Report",
            "",
            "## Summary",
            "",
            summary.strip() or "No summary provided.",
            "",
            "## Ticket",
            "",
            f"- `{ticket_path.as_posix() if ticket_path else normalized_ticket_id}`",
            "",
            "## Files Created",
            "",
            *_render_bullets(files_created, empty="None recorded."),
            "",
            "## Files Updated",
            "",
            *_render_bullets(files_updated, empty="None recorded."),
            "",
            "## Validation Results",
            "",
            *_render_bullets(validation, empty="TBD"),
            "",
            "## Deviations",
            "",
            *_render_bullets(deviations, empty="None recorded."),
            "",
            "## Follow-Up",
            "",
            *_render_bullets(follow_up, empty="None recorded."),
            "",
        ]
    )


def write_implementation_report(
    ticket_id: str,
    report: str,
    *,
    root: Path = Path("."),
    slug: str | None = None,
) -> Path:
    path = report_path_for_ticket(ticket_id, root=root, slug=slug)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report, encoding="utf-8")
    return path


def _extract_title(text: str, *, fallback: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or fallback
    return fallback


def _relative_or_none(path: Path | None) -> str:
    if path is None:
        return "-"
    try:
        return path.relative_to(Path(".")).as_posix()
    except ValueError:
        return path.as_posix()


def _render_bullets(items: tuple[str, ...], *, empty: str) -> list[str]:
    cleaned = [item.strip() for item in items if item.strip()]
    if not cleaned:
        return [empty]
    return [f"- {item}" for item in cleaned]
