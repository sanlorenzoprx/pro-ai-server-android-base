from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pro_ai_server.agent.handoff import HandoffItem, build_handoff_view

DEFAULT_VALIDATION_COMMANDS = (
    "ruff check .",
    "pytest",
    "pro-ai-server validate-release",
)


@dataclass(frozen=True)
class NextActionSelection:
    item: HandoffItem | None
    reason: str
    session_status: str | None = None
    session_note: str | None = None

    @property
    def has_ticket(self) -> bool:
        return self.item is not None


@dataclass(frozen=True)
class ExecutionPacket:
    item: HandoffItem
    ticket_text: str
    validation_commands: tuple[str, ...] = DEFAULT_VALIDATION_COMMANDS
    indexed_context: str = ""
    session_status: str | None = None
    session_note: str | None = None


def default_execution_packet_path(ticket_id: str, *, root: Path = Path(".")) -> Path:
    return root / ".agents" / "execution" / f"{ticket_id.upper()}.execution.md"


def select_next_action(
    root: Path = Path("."),
    *,
    phase: str | None = None,
    ticket_id: str | None = None,
    queue_path: Path | None = None,
    session_path: Path | None = None,
    session_policy: str = "available",
) -> NextActionSelection:
    view = build_handoff_view(root, phase=phase, ticket_id=ticket_id, queue_path=queue_path)
    if not view.items:
        return NextActionSelection(item=None, reason="No accepted unreported tickets are ready for execution.")
    normalized_policy = _validate_session_policy(session_policy)
    sessions = _sessions_by_ticket(root, session_path=session_path)
    candidates: list[tuple[int, HandoffItem, object | None]] = []
    skipped_finished = 0
    for item in view.items:
        session = sessions.get(item.ticket_id)
        status = getattr(session, "status", None)
        if normalized_policy != "all" and status == "finished":
            skipped_finished += 1
            continue
        candidates.append((_session_rank(status, normalized_policy), item, session))

    if not candidates:
        suffix = f" Skipped {skipped_finished} finished session ticket(s)." if skipped_finished else ""
        return NextActionSelection(item=None, reason=f"No session-available tickets are ready for execution.{suffix}")

    candidates.sort(key=lambda candidate: (candidate[0], candidate[1].phase, candidate[1].ticket_id))
    _, item, session = candidates[0]
    status = getattr(session, "status", None)
    note = getattr(session, "note", None)
    reason = _selection_reason(item, normalized_policy, status, skipped_finished)
    return NextActionSelection(item=item, reason=reason, session_status=status, session_note=note)


def build_execution_packet(
    root: Path = Path("."),
    *,
    phase: str | None = None,
    ticket_id: str | None = None,
    queue_path: Path | None = None,
    session_path: Path | None = None,
    session_policy: str = "available",
    indexed_context: str = "",
) -> ExecutionPacket | None:
    selection = select_next_action(
        root,
        phase=phase,
        ticket_id=ticket_id,
        queue_path=queue_path,
        session_path=session_path,
        session_policy=session_policy,
    )
    if selection.item is None:
        return None
    ticket_text = _read_ticket_text(selection.item.ticket_path)
    return ExecutionPacket(
        item=selection.item,
        ticket_text=ticket_text,
        indexed_context=indexed_context,
        session_status=selection.session_status,
        session_note=selection.session_note,
    )


def render_next_action(selection: NextActionSelection) -> str:
    lines = ["# Agent Next Action", ""]
    if selection.item is None:
        lines.extend(["- Status: idle", f"- Reason: {selection.reason}"])
        return "\n".join(lines)

    item = selection.item
    lines.extend(
        [
            "- Status: ready",
            f"- Ticket: {item.ticket_id}",
            f"- Title: {item.title}",
            f"- Phase: {item.phase}",
            f"- Path: `{item.ticket_path.as_posix()}`",
            f"- Session: {selection.session_status or 'none'}",
            f"- Reason: {selection.reason}",
        ]
    )
    return "\n".join(lines)


def render_execution_packet(packet: ExecutionPacket | None) -> str:
    if packet is None:
        return "\n".join(
            [
                "# Agent Execution Packet",
                "",
                "No accepted unreported tickets are ready for execution.",
            ]
        )

    item = packet.item
    lines = [
        "# Agent Execution Packet",
        "",
        "## Selected Ticket",
        "",
        f"- Ticket: {item.ticket_id}",
        f"- Title: {item.title}",
        f"- Phase: {item.phase}",
        f"- Ticket path: `{item.ticket_path.as_posix()}`",
        f"- Decision reason: {item.decision_reason}",
        f"- Session: {packet.session_status or 'none'}",
        "",
        "## Execution Focus",
        "",
        "- Implement only the selected ticket scope.",
        "- Preserve existing user changes and unrelated worktree edits.",
        "- Update focused tests and docs when the ticket changes behavior or workflow surface.",
        "",
        "## Ticket Text",
        "",
        packet.ticket_text.strip() or "Ticket file is empty.",
        "",
        "## Indexed Context",
        "",
        packet.indexed_context.strip() or "No indexed context included.",
        "",
        "## Validation Commands",
        "",
        *[f"- `{command}`" for command in packet.validation_commands],
        "",
        "## Completion Report",
        "",
        f"- `pro-ai-server agent report {item.ticket_id} --summary \"<summary>\"`",
        "",
    ]
    return "\n".join(lines).rstrip()


def write_execution_packet(
    packet: ExecutionPacket,
    *,
    root: Path = Path("."),
    output: Path | None = None,
) -> Path:
    path = output or default_execution_packet_path(packet.item.ticket_id, root=root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_execution_packet(packet) + "\n", encoding="utf-8")
    return path


def _read_ticket_text(path: Path) -> str:
    if not path.exists():
        return "Ticket file missing."
    return path.read_text(encoding="utf-8")


def _sessions_by_ticket(root: Path, *, session_path: Path | None) -> dict[str, object]:
    from pro_ai_server.agent.sessions import build_work_sessions

    return {session.ticket_id: session for session in build_work_sessions(root, path=session_path)}


def _validate_session_policy(policy: str) -> str:
    normalized = policy.strip().lower()
    if normalized not in ("available", "resume", "all"):
        raise ValueError("Session policy must be one of: available, resume, all.")
    return normalized


def _session_rank(status: str | None, policy: str) -> int:
    if policy == "resume":
        if status in ("picked-up", "started"):
            return 0
        if status is None:
            return 1
        return 2
    if policy == "all":
        if status is None:
            return 0
        if status in ("picked-up", "started"):
            return 1
        return 2
    if status is None:
        return 0
    return 1


def _selection_reason(item: HandoffItem, policy: str, status: str | None, skipped_finished: int) -> str:
    session_text = status or "no session"
    skipped_text = f" Skipped {skipped_finished} finished session ticket(s)." if skipped_finished else ""
    return (
        "Selected ready accepted ticket by session policy "
        f"`{policy}` and stable phase/ticket order: {item.phase}/{item.ticket_id} ({session_text}).{skipped_text}"
    )
