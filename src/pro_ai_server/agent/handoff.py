from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pro_ai_server.agent.queue import TicketDecision, build_decision_queue
from pro_ai_server.agent.reporter import AgentReport, AgentTicket, discover_reports, discover_tickets


@dataclass(frozen=True)
class HandoffItem:
    ticket_id: str
    title: str
    phase: str
    ticket_path: Path
    decision_reason: str
    report_path: Path | None = None

    @property
    def implementation_status(self) -> str:
        return "reported" if self.report_path else "ready"


@dataclass(frozen=True)
class HandoffView:
    items: tuple[HandoffItem, ...]

    @property
    def ready_count(self) -> int:
        return sum(1 for item in self.items if item.implementation_status == "ready")

    @property
    def reported_count(self) -> int:
        return sum(1 for item in self.items if item.implementation_status == "reported")


def build_handoff_view(
    root: Path = Path("."),
    *,
    phase: str | None = None,
    ticket_id: str | None = None,
    include_reported: bool = False,
    queue_path: Path | None = None,
) -> HandoffView:
    tickets = {ticket.ticket_id: ticket for ticket in discover_tickets(root)}
    reports = {report.ticket_id: report for report in discover_reports(root)}
    decisions = build_decision_queue(root, phase=phase, path=queue_path)
    normalized_ticket_id = ticket_id.upper() if ticket_id else None

    items: list[HandoffItem] = []
    for decision in decisions:
        if decision.decision != "accepted":
            continue
        if normalized_ticket_id and decision.ticket_id != normalized_ticket_id:
            continue
        ticket = tickets.get(decision.ticket_id)
        if ticket is None:
            continue
        report = reports.get(decision.ticket_id)
        if report and not include_reported:
            continue
        items.append(_build_item(ticket, decision, report))

    items.sort(key=lambda item: (item.phase, item.ticket_id))
    return HandoffView(items=tuple(items))


def render_handoff_view(view: HandoffView) -> str:
    lines = [
        "# Agent Implementation Handoff",
        "",
        f"- Ready: {view.ready_count}",
        f"- Reported: {view.reported_count}",
        "",
    ]
    if not view.items:
        lines.append("No accepted tickets need implementation.")
        return "\n".join(lines)

    for index, item in enumerate(view.items, start=1):
        lines.extend(
            [
                f"## {index}. {item.ticket_id} {item.title}",
                "",
                f"- Status: {item.implementation_status}",
                f"- Phase: {item.phase}",
                f"- Ticket: `{item.ticket_path.as_posix()}`",
                f"- Decision reason: {item.decision_reason}",
            ]
        )
        if item.report_path:
            lines.append(f"- Report: `{item.report_path.as_posix()}`")
        lines.extend(
            [
                "",
                "### Next Steps",
                "",
                "- Read the ticket objective and acceptance criteria.",
                "- Gather context with `pro-ai-server agent context \"<ticket id or title>\"` if needed.",
                "- Implement only the ticket-scoped change.",
                "- Record validation evidence with `pro-ai-server agent report`.",
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def _build_item(ticket: AgentTicket, decision: TicketDecision, report: AgentReport | None) -> HandoffItem:
    return HandoffItem(
        ticket_id=ticket.ticket_id,
        title=_clean_title(ticket.title, ticket.ticket_id),
        phase=ticket.phase,
        ticket_path=ticket.path,
        decision_reason=decision.reason,
        report_path=report.path if report else None,
    )


def _clean_title(title: str, ticket_id: str) -> str:
    return title.removeprefix(ticket_id).strip() or title
