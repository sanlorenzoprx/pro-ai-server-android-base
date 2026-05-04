from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from pro_ai_server.rag.chunker import chunk_text_by_lines, language_for_path, should_index_file
from pro_ai_server.rag.store import IndexStore


DEFAULT_INDEX_PATH = Path(".pro-ai-server") / "index.sqlite"


@dataclass(frozen=True)
class IndexResult:
    file_count: int
    chunk_count: int
    db_path: Path


def index_project(root: Path, *, db_path: Path | None = None) -> IndexResult:
    project_root = root.resolve()
    target_db = db_path or project_root / DEFAULT_INDEX_PATH
    store = IndexStore(target_db)
    store.initialize()
    current_paths: set[Path] = set()
    for path in sorted(project_root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(project_root)
        if not should_index_file(relative):
            continue
        current_paths.add(relative)
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        stat = path.stat()
        chunks = tuple((chunk.text, chunk.start_line, chunk.end_line) for chunk in chunk_text_by_lines(text))
        store.replace_file(
            path=relative,
            language=language_for_path(relative),
            sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
            mtime=stat.st_mtime,
            size=stat.st_size,
            chunks=chunks,
        )
    store.delete_missing_files(current_paths)
    status = store.status()
    return IndexResult(file_count=status.file_count, chunk_count=status.chunk_count, db_path=target_db)
