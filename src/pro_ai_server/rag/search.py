from __future__ import annotations

from pathlib import Path

from pro_ai_server.rag.indexer import DEFAULT_INDEX_PATH
from pro_ai_server.rag.store import IndexStore, SearchResult


def search_index(query: str, *, db_path: Path = DEFAULT_INDEX_PATH, limit: int = 5) -> tuple[SearchResult, ...]:
    return IndexStore(db_path).search(query, limit=limit)

