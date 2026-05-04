from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pro_ai_server.agent.reporter import AgentReport, AgentTicket, discover_reports, discover_tickets
from pro_ai_server.agent.sessions import WorkSession, build_work_sessions

ACTIVE_SESSION_STATUSES = ("picked-up", "started")


@dataclass(frozen=True)
class SessionReportWarning:
    ticket_id: str
    code: str
    message: str
    session_status: str
    phase: str | None = None
    ticket_path: Path | None = None
    report_path: Path | None = None
    packet_path: Path | None = None


@dataclass(frozen=True)
class SessionReportReconciliation:
    warnings: tuple[SessionReportWarning, ...]

    @property
    def warning_count(self) -> int:
        return len(self.warnings)


def build_session_report_reconciliation(
    root: Path = Path("."),
    *,
    phase: str | None = None,
    ticket_id: str | None = None,
    session_path: Path | None = None,
) -> SessionReportReconciliation:
    tickets = {ticket.ticket_id: ticket for ticket in discover_tickets(root)}
    reports = {report.ticket_id: report for report in discover_reports(root)}
    sessions = build_work_sessions(root, phase=phase, ticket_id=ticket_id, path=session_path)

    warnings: list[SessionReportWarning] = []
    for session in sessions:
        ticket = tickets.get(session.ticket_id)
        report = reports.get(session.ticket_id)
        if ticket is None:
            warnings.append(_orphan_session_warning(session))
            continue
        if session.status in ACTIVE_SESSION_STATUSES and report:
            warnings.append(_active_reported_warning(session, ticket, report))
        elif session.status == "finished" and report:
            warnings.append(_finished_reported_warning(session, ticket, report))
        elif session.status == "finished":
            warnings.append(_finished_unreported_warning(session, ticket))

    warnings.sort(key=lambda warning: (warning.phase or "", warning.ticket_id, warning.code))
    return SessionReportReconciliation(warnings=tuple(warnings))


def render_session_report_reconciliation(reconciliation: SessionReportReconciliation) -> str:
    lines = [
        "# Agent Session Report Reconciliation",
        "",
        f"- Warnings: {reconciliation.warning_count}",
        "",
        "| Ticket | Code | Session | Phase | Report | Packet | Message |",
        "|---|---|---|---|---|---|---|",
    ]
    if not reconciliation.warnings:
        lines.append("| none | none | none | none | none | none | none |")
    for warning in reconciliation.warnings:
        lines.append(
            f"| {warning.ticket_id} | {warning.code} | {warning.session_status} | {warning.phase or '-'} | "
            f"{_relative_or_none(warning.report_path)} | {_relative_or_none(warning.packet_path)} | "
            f"{_escape_cell(warning.message)} |"
        )
    return "\n".join(lines)


def _active_reported_warning(
    session: WorkSession,
    ticket: AgentTicket,
    report: AgentReport,
) -> SessionReportWarning:
    return SessionReportWarning(
        ticket_id=session.ticket_id,
        code="active-session-reported",
        message="Session is active but an implementation report exists; finish or reconcile the session before autopilot continues.",
        session_status=session.status,
        phase=ticket.phase,
        ticket_path=ticket.path,
        report_path=report.path,
        packet_path=session.packet_path,
    )


def _finished_reported_warning(
    session: WorkSession,
    ticket: AgentTicket,
    report: AgentReport,
) -> SessionReportWarning:
    return SessionReportWarning(
        ticket_id=session.ticket_id,
        code="finished-session-reported",
        message="Session is finished and reported; archive or clear lingering session state before long-running autopilot.",
        session_status=session.status,
        phase=ticket.phase,
        ticket_path=ticket.path,
        report_path=report.path,
        packet_path=session.packet_path,
    )


def _finished_unreported_warning(session: WorkSession, ticket: AgentTicket) -> SessionReportWarning:
    return SessionReportWarning(
        ticket_id=session.ticket_id,
        code="finished-session-unreported",
        message="Session is finished but no implementation report exists; write the report before considering the ticket closed.",
        session_status=session.status,
        phase=ticket.phase,
        ticket_path=ticket.path,
        packet_path=session.packet_path,
    )


def _orphan_session_warning(session: WorkSession) -> SessionReportWarning:
    return SessionReportWarning(
        ticket_id=session.ticket_id,
        code="orphan-session",
        message="Session references a ticket that no longer exists in build tickets.",
        session_status=session.status,
        phase=session.phase,
        ticket_path=session.ticket_path,
        packet_path=session.packet_path,
    )


def _relative_or_none(path: Path | None) -> str:
    if path is None:
        return "-"
    try:
        return path.relative_to(Path(".")).as_posix()
    except ValueError:
        return path.as_posix()


def _escape_cell(text: str) -> str:
    return text.replace("|", "\\|")
