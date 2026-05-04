from __future__ import annotations

from pathlib import Path

from pro_ai_server.rag.context import build_context
from pro_ai_server.rag.indexer import DEFAULT_INDEX_PATH


def build_agent_context(
    query: str,
    *,
    root: Path = Path("."),
    db_path: Path = DEFAULT_INDEX_PATH,
    limit: int = 5,
    max_chars: int = 12000,
) -> str:
    memory = _read_project_memory(root)
    try:
        return build_context(query, db_path=db_path, project_summary=memory, limit=limit, max_chars=max_chars)
    except Exception:  # noqa: BLE001 - agent drafts should still work before indexing.
        parts = ["# Project Context"]
        if memory:
            parts.extend(["", memory.strip()])
        parts.extend(["", "No indexed context found. Run `pro-ai-server index .`."])
        return "\n".join(parts)[:max_chars]


def _read_project_memory(root: Path) -> str:
    path = root / ".agents" / "memory" / "project-memory.md"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")
