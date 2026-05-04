from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pro_ai_server.agent.reporter import AgentTicket, discover_tickets

VALID_DECISIONS = ("accepted", "deferred", "rejected")


@dataclass(frozen=True)
class TicketDecision:
    ticket_id: str
    decision: str
    reason: str
    ticket_path: Path | None = None
    phase: str | None = None


@dataclass(frozen=True)
class TicketDecisionEvent:
    sequence: int
    ticket_id: str
    decision: str
    reason: str
    ticket_path: Path | None = None
    phase: str | None = None


def default_decision_path(root: Path = Path(".")) -> Path:
    return root / ".agents" / "queue" / "ticket-decisions.json"


def default_decision_ledger_path(root: Path = Path(".")) -> Path:
    return root / ".agents" / "queue" / "ticket-decisions.jsonl"


def validate_decision(decision: str) -> str:
    normalized = decision.strip().lower()
    if normalized not in VALID_DECISIONS:
        allowed = ", ".join(VALID_DECISIONS)
        raise ValueError(f"Decision must be one of: {allowed}.")
    return normalized


def load_decisions(path: Path) -> tuple[TicketDecision, ...]:
    if not path.exists():
        return ()
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = payload.get("decisions", [])
    decisions: list[TicketDecision] = []
    for record in records:
        ticket_path = Path(record["ticket_path"]) if record.get("ticket_path") else None
        decisions.append(
            TicketDecision(
                ticket_id=str(record["ticket_id"]).upper(),
                decision=validate_decision(str(record["decision"])),
                reason=str(record.get("reason", "")),
                ticket_path=ticket_path,
                phase=record.get("phase"),
            )
        )
    return tuple(sorted(decisions, key=lambda item: item.ticket_id))


def load_decision_events(path: Path) -> tuple[TicketDecisionEvent, ...]:
    if not path.exists():
        return ()
    events: list[TicketDecisionEvent] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        ticket_path = Path(record["ticket_path"]) if record.get("ticket_path") else None
        events.append(
            TicketDecisionEvent(
                sequence=int(record["sequence"]),
                ticket_id=str(record["ticket_id"]).upper(),
                decision=validate_decision(str(record["decision"])),
                reason=str(record.get("reason", "")),
                ticket_path=ticket_path,
                phase=record.get("phase"),
            )
        )
    return tuple(sorted(events, key=lambda event: (event.sequence, event.ticket_id)))


def save_decisions(path: Path, decisions: tuple[TicketDecision, ...]) -> Path:
    payload = {
        "decisions": [
            {
                "ticket_id": decision.ticket_id,
                "decision": decision.decision,
                "reason": decision.reason,
                "ticket_path": decision.ticket_path.as_posix() if decision.ticket_path else None,
                "phase": decision.phase,
            }
            for decision in sorted(decisions, key=lambda item: item.ticket_id)
        ]
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def append_decision_event(path: Path, event: TicketDecisionEvent) -> Path:
    payload = {
        "decision": event.decision,
        "phase": event.phase,
        "reason": event.reason,
        "sequence": event.sequence,
        "ticket_id": event.ticket_id,
        "ticket_path": event.ticket_path.as_posix() if event.ticket_path else None,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")
    return path


def current_decisions_from_events(events: tuple[TicketDecisionEvent, ...]) -> tuple[TicketDecision, ...]:
    latest: dict[str, TicketDecisionEvent] = {}
    for event in sorted(events, key=lambda item: (item.sequence, item.ticket_id)):
        latest[event.ticket_id] = event
    return tuple(
        sorted(
            (
                TicketDecision(
                    ticket_id=event.ticket_id,
                    decision=event.decision,
                    reason=event.reason,
                    ticket_path=event.ticket_path,
                    phase=event.phase,
                )
                for event in latest.values()
            ),
            key=lambda item: item.ticket_id,
        )
    )


def record_decision(
    ticket_id: str,
    *,
    decision: str,
    reason: str,
    root: Path = Path("."),
    path: Path | None = None,
    ledger_path: Path | None = None,
) -> TicketDecision:
    normalized_ticket_id = ticket_id.strip().upper()
    normalized_decision = validate_decision(decision)
    decision_path = path or default_decision_path(root)
    ledger = ledger_path or default_decision_ledger_path(root)
    events = load_decision_events(ledger)
    ticket = _ticket_by_id(root, normalized_ticket_id)
    event = TicketDecisionEvent(
        sequence=max((item.sequence for item in events), default=0) + 1,
        ticket_id=normalized_ticket_id,
        decision=normalized_decision,
        reason=reason.strip() or "No reason recorded.",
        ticket_path=ticket.path if ticket else None,
        phase=ticket.phase if ticket else None,
    )
    append_decision_event(ledger, event)
    decisions = current_decisions_from_events((*events, event))
    save_decisions(decision_path, decisions)
    return next(item for item in decisions if item.ticket_id == normalized_ticket_id)


def build_decision_queue(root: Path = Path("."), *, phase: str | None = None, path: Path | None = None) -> tuple[TicketDecision, ...]:
    decision_path = path or default_decision_path(root)
    decisions = load_decisions(decision_path)
    if phase is None:
        return decisions
    return tuple(decision for decision in decisions if decision.phase == phase)


def render_decision_queue(decisions: tuple[TicketDecision, ...]) -> str:
    lines = [
        "# Agent Ticket Decision Queue",
        "",
        f"- Accepted: {_count(decisions, 'accepted')}",
        f"- Deferred: {_count(decisions, 'deferred')}",
        f"- Rejected: {_count(decisions, 'rejected')}",
        "",
        "| Ticket | Decision | Phase | Reason |",
        "|---|---|---|---|",
    ]
    if not decisions:
        lines.append("| none | none | none | none |")
    for decision in decisions:
        lines.append(
            f"| {decision.ticket_id} | {decision.decision} | {decision.phase or '-'} | {_escape_cell(decision.reason)} |"
        )
    return "\n".join(lines)


def render_decision_history(events: tuple[TicketDecisionEvent, ...]) -> str:
    lines = [
        "# Agent Ticket Decision History",
        "",
        f"- Events: {len(events)}",
        "",
        "| Seq | Ticket | Decision | Phase | Reason |",
        "|---|---|---|---|---|",
    ]
    if not events:
        lines.append("| none | none | none | none | none |")
    for event in events:
        lines.append(
            f"| {event.sequence} | {event.ticket_id} | {event.decision} | {event.phase or '-'} | {_escape_cell(event.reason)} |"
        )
    return "\n".join(lines)


def _ticket_by_id(root: Path, ticket_id: str) -> AgentTicket | None:
    return next((ticket for ticket in discover_tickets(root) if ticket.ticket_id == ticket_id), None)


def _count(decisions: tuple[TicketDecision, ...], decision: str) -> int:
    return sum(1 for item in decisions if item.decision == decision)


def _escape_cell(text: str) -> str:
    return text.replace("|", "\\|")
