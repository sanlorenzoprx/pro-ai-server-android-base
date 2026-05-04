from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pro_ai_server.agent.execution import (
    DEFAULT_VALIDATION_COMMANDS,
    build_execution_packet,
    select_next_action,
    write_execution_packet,
)
from pro_ai_server.agent.reconciliation import build_session_report_reconciliation
from pro_ai_server.agent.sessions import build_work_sessions, record_session_event

ACTIVE_SESSION_STATUSES = ("picked-up", "started")


@dataclass(frozen=True)
class AutopilotResult:
    mode: str
    status: str
    stop_reason: str
    max_tickets: int
    ticket_id: str | None = None
    phase: str | None = None
    packet_path: Path | None = None
    session_events: tuple[str, ...] = ()
    validation_commands: tuple[str, ...] = DEFAULT_VALIDATION_COMMANDS
    report_command: str | None = None
    reconciliation_warnings: int = 0
    actions: tuple[str, ...] = ()


def run_autopilot_once(
    root: Path = Path("."),
    *,
    phase: str | None = None,
    ticket_id: str | None = None,
    queue_path: Path | None = None,
    session_path: Path | None = None,
    session_ledger_path: Path | None = None,
    session_policy: str = "available",
    max_tickets: int = 1,
    execute: bool = False,
    start_session: bool = False,
) -> AutopilotResult:
    if max_tickets < 1:
        return AutopilotResult(
            mode=_mode(execute),
            status="stopped",
            stop_reason="max-tickets must be at least 1.",
            max_tickets=max_tickets,
        )

    reconciliation = build_session_report_reconciliation(
        root,
        phase=phase,
        ticket_id=ticket_id,
        session_path=session_path,
    )
    if reconciliation.warning_count:
        return AutopilotResult(
            mode=_mode(execute),
            status="stopped",
            stop_reason="Reconciliation warnings must be resolved before autopilot continues.",
            max_tickets=max_tickets,
            reconciliation_warnings=reconciliation.warning_count,
            actions=("Run `pro-ai-server agent reconcile --fail-on-warning` for details.",),
        )

    active_sessions = tuple(
        session
        for session in build_work_sessions(root, phase=phase, ticket_id=ticket_id, path=session_path)
        if session.status in ACTIVE_SESSION_STATUSES
    )
    if active_sessions and session_policy != "resume":
        ticket_list = ", ".join(session.ticket_id for session in active_sessions)
        return AutopilotResult(
            mode=_mode(execute),
            status="stopped",
            stop_reason=f"Active work session(s) exist: {ticket_list}. Use --session-policy resume to continue active work.",
            max_tickets=max_tickets,
            actions=("Review `pro-ai-server agent sessions` before starting another ticket.",),
        )

    selection = select_next_action(
        root,
        phase=phase,
        ticket_id=ticket_id,
        queue_path=queue_path,
        session_path=session_path,
        session_policy=session_policy,
    )
    if selection.item is None:
        return AutopilotResult(
            mode=_mode(execute),
            status="stopped",
            stop_reason=selection.reason,
            max_tickets=max_tickets,
        )

    packet = build_execution_packet(
        root,
        phase=phase,
        ticket_id=ticket_id,
        queue_path=queue_path,
        session_path=session_path,
        session_policy=session_policy,
    )
    assert packet is not None
    actions = [
        f"Selected {packet.item.ticket_id}.",
        "Generated focused execution packet content.",
    ]
    packet_path = None
    session_events: list[str] = []
    if execute:
        packet_path = write_execution_packet(packet, root=root)
        actions.append(f"Wrote execution packet: {packet_path.as_posix()}.")
        if start_session:
            record_session_event(
                packet.item.ticket_id,
                event="picked-up",
                note="Autopilot picked up execution packet.",
                root=root,
                path=session_path,
                ledger_path=session_ledger_path,
                packet_path=packet_path,
            )
            record_session_event(
                packet.item.ticket_id,
                event="started",
                note="Autopilot started controlled execution session.",
                root=root,
                path=session_path,
                ledger_path=session_ledger_path,
                packet_path=packet_path,
            )
            session_events.extend(["picked-up", "started"])
            actions.append("Recorded picked-up and started session events.")
    else:
        actions.append("Preview only; no files or sessions were written.")

    actions.append("Stop for implementation, validation, and implementation report.")
    return AutopilotResult(
        mode=_mode(execute),
        status="ready" if not execute else "stopped",
        stop_reason="Preview complete." if not execute else "Implementation required before the next autopilot tick.",
        max_tickets=max_tickets,
        ticket_id=packet.item.ticket_id,
        phase=packet.item.phase,
        packet_path=packet_path,
        session_events=tuple(session_events),
        validation_commands=packet.validation_commands,
        report_command=f'pro-ai-server agent report {packet.item.ticket_id} --summary "<summary>"',
        actions=tuple(actions),
    )


def render_autopilot_result(result: AutopilotResult) -> str:
    lines = [
        "# Agent Autopilot",
        "",
        f"- Mode: {result.mode}",
        f"- Status: {result.status}",
        f"- Stop reason: {result.stop_reason}",
        f"- Max tickets: {result.max_tickets}",
        f"- Reconciliation warnings: {result.reconciliation_warnings}",
        f"- Ticket: {result.ticket_id or '-'}",
        f"- Phase: {result.phase or '-'}",
        f"- Packet: {_relative_or_none(result.packet_path)}",
        f"- Session events: {', '.join(result.session_events) if result.session_events else '-'}",
        "",
        "## Actions",
        "",
        *_render_bullets(result.actions, empty="None."),
        "",
        "## Validation Gate",
        "",
        *_render_bullets(tuple(f"`{command}`" for command in result.validation_commands), empty="No validation commands."),
        "",
        "## Report Gate",
        "",
        f"- `{result.report_command}`" if result.report_command else "- No report command.",
    ]
    return "\n".join(lines)


def _mode(execute: bool) -> str:
    return "execute" if execute else "preview"


def _relative_or_none(path: Path | None) -> str:
    if path is None:
        return "-"
    try:
        return path.relative_to(Path(".")).as_posix()
    except ValueError:
        return path.as_posix()


def _render_bullets(items: tuple[str, ...], *, empty: str) -> list[str]:
    if not items:
        return [f"- {empty}"]
    return [f"- {item}" for item in items]
