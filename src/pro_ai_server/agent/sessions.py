from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pro_ai_server.agent.execution import default_execution_packet_path
from pro_ai_server.agent.reporter import AgentTicket, discover_tickets

VALID_SESSION_EVENTS = ("picked-up", "started", "finished")
SESSION_EVENT_ALIASES = {
    "pickup": "picked-up",
    "picked-up": "picked-up",
    "start": "started",
    "started": "started",
    "finish": "finished",
    "finished": "finished",
}


@dataclass(frozen=True)
class WorkSession:
    ticket_id: str
    status: str
    note: str
    sequence: int
    packet_path: Path | None = None
    ticket_path: Path | None = None
    phase: str | None = None


@dataclass(frozen=True)
class WorkSessionEvent:
    sequence: int
    ticket_id: str
    event: str
    note: str
    packet_path: Path | None = None
    ticket_path: Path | None = None
    phase: str | None = None


def default_session_path(root: Path = Path(".")) -> Path:
    return root / ".agents" / "execution" / "work-sessions.json"


def default_session_ledger_path(root: Path = Path(".")) -> Path:
    return root / ".agents" / "execution" / "work-sessions.jsonl"


def validate_session_event(event: str) -> str:
    normalized = event.strip().lower()
    if normalized not in SESSION_EVENT_ALIASES:
        allowed = ", ".join(VALID_SESSION_EVENTS)
        raise ValueError(f"Session event must be one of: {allowed}.")
    return SESSION_EVENT_ALIASES[normalized]


def load_sessions(path: Path) -> tuple[WorkSession, ...]:
    if not path.exists():
        return ()
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = payload.get("sessions", [])
    sessions: list[WorkSession] = []
    for record in records:
        sessions.append(
            WorkSession(
                ticket_id=str(record["ticket_id"]).upper(),
                status=validate_session_event(str(record["status"])),
                note=str(record.get("note", "")),
                sequence=int(record["sequence"]),
                packet_path=Path(record["packet_path"]) if record.get("packet_path") else None,
                ticket_path=Path(record["ticket_path"]) if record.get("ticket_path") else None,
                phase=record.get("phase"),
            )
        )
    return tuple(sorted(sessions, key=lambda item: (item.phase or "", item.ticket_id)))


def load_session_events(path: Path) -> tuple[WorkSessionEvent, ...]:
    if not path.exists():
        return ()
    events: list[WorkSessionEvent] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        events.append(
            WorkSessionEvent(
                sequence=int(record["sequence"]),
                ticket_id=str(record["ticket_id"]).upper(),
                event=validate_session_event(str(record["event"])),
                note=str(record.get("note", "")),
                packet_path=Path(record["packet_path"]) if record.get("packet_path") else None,
                ticket_path=Path(record["ticket_path"]) if record.get("ticket_path") else None,
                phase=record.get("phase"),
            )
        )
    return tuple(sorted(events, key=lambda item: (item.sequence, item.ticket_id)))


def save_sessions(path: Path, sessions: tuple[WorkSession, ...]) -> Path:
    payload = {
        "sessions": [
            {
                "note": session.note,
                "packet_path": session.packet_path.as_posix() if session.packet_path else None,
                "phase": session.phase,
                "sequence": session.sequence,
                "status": session.status,
                "ticket_id": session.ticket_id,
                "ticket_path": session.ticket_path.as_posix() if session.ticket_path else None,
            }
            for session in sorted(sessions, key=lambda item: item.ticket_id)
        ]
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def append_session_event(path: Path, event: WorkSessionEvent) -> Path:
    payload = {
        "event": event.event,
        "note": event.note,
        "packet_path": event.packet_path.as_posix() if event.packet_path else None,
        "phase": event.phase,
        "sequence": event.sequence,
        "ticket_id": event.ticket_id,
        "ticket_path": event.ticket_path.as_posix() if event.ticket_path else None,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")
    return path


def current_sessions_from_events(events: tuple[WorkSessionEvent, ...]) -> tuple[WorkSession, ...]:
    latest: dict[str, WorkSessionEvent] = {}
    for event in sorted(events, key=lambda item: (item.sequence, item.ticket_id)):
        latest[event.ticket_id] = event
    return tuple(
        sorted(
            (
                WorkSession(
                    ticket_id=event.ticket_id,
                    status=event.event,
                    note=event.note,
                    sequence=event.sequence,
                    packet_path=event.packet_path,
                    ticket_path=event.ticket_path,
                    phase=event.phase,
                )
                for event in latest.values()
            ),
            key=lambda item: (item.phase or "", item.ticket_id),
        )
    )


def record_session_event(
    ticket_id: str,
    *,
    event: str,
    note: str = "",
    root: Path = Path("."),
    path: Path | None = None,
    ledger_path: Path | None = None,
    packet_path: Path | None = None,
) -> WorkSession:
    normalized_ticket_id = ticket_id.strip().upper()
    normalized_event = validate_session_event(event)
    session_path = path or default_session_path(root)
    ledger = ledger_path or default_session_ledger_path(root)
    events = load_session_events(ledger)
    ticket = _ticket_by_id(root, normalized_ticket_id)
    packet = packet_path or default_execution_packet_path(normalized_ticket_id, root=root)
    if not packet.exists():
        packet = None
    record = WorkSessionEvent(
        sequence=max((item.sequence for item in events), default=0) + 1,
        ticket_id=normalized_ticket_id,
        event=normalized_event,
        note=note.strip() or "No note recorded.",
        packet_path=packet,
        ticket_path=ticket.path if ticket else None,
        phase=ticket.phase if ticket else None,
    )
    append_session_event(ledger, record)
    sessions = current_sessions_from_events((*events, record))
    save_sessions(session_path, sessions)
    return next(item for item in sessions if item.ticket_id == normalized_ticket_id)


def build_work_sessions(
    root: Path = Path("."),
    *,
    phase: str | None = None,
    ticket_id: str | None = None,
    path: Path | None = None,
) -> tuple[WorkSession, ...]:
    sessions = load_sessions(path or default_session_path(root))
    normalized_ticket_id = ticket_id.upper() if ticket_id else None
    return tuple(
        session
        for session in sessions
        if (phase is None or session.phase == phase) and (normalized_ticket_id is None or session.ticket_id == normalized_ticket_id)
    )


def render_work_sessions(sessions: tuple[WorkSession, ...]) -> str:
    lines = [
        "# Agent Work Sessions",
        "",
        f"- Picked up: {_count_sessions(sessions, 'picked-up')}",
        f"- Started: {_count_sessions(sessions, 'started')}",
        f"- Finished: {_count_sessions(sessions, 'finished')}",
        "",
        "| Ticket | Status | Phase | Packet | Note |",
        "|---|---|---|---|---|",
    ]
    if not sessions:
        lines.append("| none | none | none | none | none |")
    for session in sessions:
        lines.append(
            f"| {session.ticket_id} | {session.status} | {session.phase or '-'} | "
            f"{_relative_or_none(session.packet_path)} | {_escape_cell(session.note)} |"
        )
    return "\n".join(lines)


def render_session_history(events: tuple[WorkSessionEvent, ...]) -> str:
    lines = [
        "# Agent Work Session History",
        "",
        f"- Events: {len(events)}",
        "",
        "| Seq | Ticket | Event | Phase | Packet | Note |",
        "|---|---|---|---|---|---|",
    ]
    if not events:
        lines.append("| none | none | none | none | none | none |")
    for event in events:
        lines.append(
            f"| {event.sequence} | {event.ticket_id} | {event.event} | {event.phase or '-'} | "
            f"{_relative_or_none(event.packet_path)} | {_escape_cell(event.note)} |"
        )
    return "\n".join(lines)


def _ticket_by_id(root: Path, ticket_id: str) -> AgentTicket | None:
    return next((ticket for ticket in discover_tickets(root) if ticket.ticket_id == ticket_id), None)


def _count_sessions(sessions: tuple[WorkSession, ...], status: str) -> int:
    return sum(1 for item in sessions if item.status == status)


def _relative_or_none(path: Path | None) -> str:
    if path is None:
        return "-"
    try:
        return path.relative_to(Path(".")).as_posix()
    except ValueError:
        return path.as_posix()


def _escape_cell(text: str) -> str:
    return text.replace("|", "\\|")
