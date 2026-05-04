from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pro_ai_server.agent.reconciliation import build_session_report_reconciliation
from pro_ai_server.agent.sessions import WorkSession, default_session_path, load_sessions, save_sessions

ARCHIVABLE_WARNING_CODE = "finished-session-reported"


@dataclass(frozen=True)
class SessionArchiveItem:
    ticket_id: str
    status: str
    phase: str | None
    sequence: int
    note: str
    packet_path: Path | None = None
    ticket_path: Path | None = None
    report_path: Path | None = None


@dataclass(frozen=True)
class SessionArchivePlan:
    items: tuple[SessionArchiveItem, ...]
    current_session_path: Path
    archive_path: Path
    write: bool = False

    @property
    def archive_count(self) -> int:
        return len(self.items)


def default_session_archive_path(root: Path = Path(".")) -> Path:
    return root / ".agents" / "execution" / "archived-work-sessions.jsonl"


def build_session_archive_plan(
    root: Path = Path("."),
    *,
    phase: str | None = None,
    ticket_id: str | None = None,
    session_path: Path | None = None,
    archive_path: Path | None = None,
    write: bool = False,
) -> SessionArchivePlan:
    current_path = session_path or default_session_path(root)
    archive = archive_path or default_session_archive_path(root)
    sessions = {session.ticket_id: session for session in load_sessions(current_path)}
    reconciliation = build_session_report_reconciliation(root, phase=phase, ticket_id=ticket_id, session_path=current_path)
    items: list[SessionArchiveItem] = []
    for warning in reconciliation.warnings:
        if warning.code != ARCHIVABLE_WARNING_CODE:
            continue
        session = sessions.get(warning.ticket_id)
        if session is None:
            continue
        items.append(_archive_item(session, report_path=warning.report_path))
    items.sort(key=lambda item: (item.phase or "", item.ticket_id))
    return SessionArchivePlan(items=tuple(items), current_session_path=current_path, archive_path=archive, write=write)


def apply_session_archive_plan(plan: SessionArchivePlan) -> SessionArchivePlan:
    if not plan.items:
        return SessionArchivePlan(
            items=(),
            current_session_path=plan.current_session_path,
            archive_path=plan.archive_path,
            write=True,
        )
    archived_ids = {item.ticket_id for item in plan.items}
    remaining = tuple(session for session in load_sessions(plan.current_session_path) if session.ticket_id not in archived_ids)
    save_sessions(plan.current_session_path, remaining)
    _append_archive_items(plan.archive_path, plan.items)
    return SessionArchivePlan(
        items=plan.items,
        current_session_path=plan.current_session_path,
        archive_path=plan.archive_path,
        write=True,
    )


def render_session_archive_plan(plan: SessionArchivePlan) -> str:
    lines = [
        "# Agent Session Archive",
        "",
        f"- Mode: {'write' if plan.write else 'preview'}",
        f"- Archive candidates: {plan.archive_count}",
        f"- Current sessions: `{plan.current_session_path.as_posix()}`",
        f"- Archive ledger: `{plan.archive_path.as_posix()}`",
        "",
        "| Ticket | Status | Phase | Report | Packet | Note |",
        "|---|---|---|---|---|---|",
    ]
    if not plan.items:
        lines.append("| none | none | none | none | none | none |")
    for item in plan.items:
        lines.append(
            f"| {item.ticket_id} | {item.status} | {item.phase or '-'} | "
            f"{_relative_or_none(item.report_path)} | {_relative_or_none(item.packet_path)} | {_escape_cell(item.note)} |"
        )
    return "\n".join(lines)


def _archive_item(session: WorkSession, *, report_path: Path | None) -> SessionArchiveItem:
    return SessionArchiveItem(
        ticket_id=session.ticket_id,
        status=session.status,
        phase=session.phase,
        sequence=session.sequence,
        note=session.note,
        packet_path=session.packet_path,
        ticket_path=session.ticket_path,
        report_path=report_path,
    )


def _append_archive_items(path: Path, items: tuple[SessionArchiveItem, ...]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for item in items:
            payload = {
                "note": item.note,
                "packet_path": item.packet_path.as_posix() if item.packet_path else None,
                "phase": item.phase,
                "report_path": item.report_path.as_posix() if item.report_path else None,
                "sequence": item.sequence,
                "status": item.status,
                "ticket_id": item.ticket_id,
                "ticket_path": item.ticket_path.as_posix() if item.ticket_path else None,
            }
            handle.write(json.dumps(payload, sort_keys=True) + "\n")
    return path


def _relative_or_none(path: Path | None) -> str:
    if path is None:
        return "-"
    try:
        return path.relative_to(Path(".")).as_posix()
    except ValueError:
        return path.as_posix()


def _escape_cell(text: str) -> str:
    return text.replace("|", "\\|")
