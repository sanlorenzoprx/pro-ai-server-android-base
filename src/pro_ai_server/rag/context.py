from __future__ import annotations

from pathlib import Path

from pro_ai_server.rag.indexer import DEFAULT_INDEX_PATH
from pro_ai_server.rag.search import search_index


def build_context(
    query: str,
    *,
    db_path: Path = DEFAULT_INDEX_PATH,
    project_summary: str = "",
    limit: int = 5,
    max_chars: int = 6000,
) -> str:
    parts = ["# Project Context"]
    if project_summary:
        parts.extend(["", project_summary.strip()])
    for result in search_index(query, db_path=db_path, limit=limit):
        parts.extend(
            [
                "",
                f"## {result.path.as_posix()}:{result.start_line}-{result.end_line} chunk {result.chunk_index}",
                result.text,
                "---",
            ]
        )
    return "\n".join(parts)[:max_chars]
