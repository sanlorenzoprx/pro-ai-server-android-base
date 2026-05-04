from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class IndexStatus:
    file_count: int
    chunk_count: int


@dataclass(frozen=True)
class SearchResult:
    path: Path
    language: str
    chunk_index: int
    start_line: int
    end_line: int
    text: str
    score: int


class IndexStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS files (path TEXT PRIMARY KEY, language TEXT, sha256 TEXT, mtime REAL, size INTEGER)"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS chunks (path TEXT, chunk_index INTEGER, text TEXT, PRIMARY KEY(path, chunk_index))"
            )
            _ensure_column(conn, "chunks", "start_line", "INTEGER DEFAULT 1")
            _ensure_column(conn, "chunks", "end_line", "INTEGER DEFAULT 1")

    def replace_file(
        self,
        *,
        path: Path,
        language: str,
        sha256: str,
        mtime: float,
        size: int,
        chunks: tuple[tuple[str, int, int], ...],
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO files(path, language, sha256, mtime, size) VALUES (?, ?, ?, ?, ?)",
                (path.as_posix(), language, sha256, mtime, size),
            )
            conn.execute("DELETE FROM chunks WHERE path = ?", (path.as_posix(),))
            conn.executemany(
                "INSERT INTO chunks(path, chunk_index, text, start_line, end_line) VALUES (?, ?, ?, ?, ?)",
                (
                    (path.as_posix(), index, chunk_text, start_line, end_line)
                    for index, (chunk_text, start_line, end_line) in enumerate(chunks)
                ),
            )

    def delete_missing_files(self, current_paths: set[Path]) -> int:
        current = {path.as_posix() for path in current_paths}
        with self._connect() as conn:
            existing = {row[0] for row in conn.execute("SELECT path FROM files").fetchall()}
            missing = existing - current
            for path in missing:
                conn.execute("DELETE FROM chunks WHERE path = ?", (path,))
                conn.execute("DELETE FROM files WHERE path = ?", (path,))
        return len(missing)

    def status(self) -> IndexStatus:
        with self._connect() as conn:
            file_count = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
            chunk_count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        return IndexStatus(file_count=file_count, chunk_count=chunk_count)

    def search(self, query: str, *, limit: int = 5) -> tuple[SearchResult, ...]:
        terms = [term.lower() for term in query.split() if term.strip()]
        if not terms:
            return ()
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT c.path, f.language, c.chunk_index, c.start_line, c.end_line, c.text FROM chunks c JOIN files f ON c.path = f.path"
            ).fetchall()
        results = []
        for path, language, chunk_index, start_line, end_line, text in rows:
            lowered = text.lower()
            score = sum(lowered.count(term) for term in terms)
            if score:
                results.append(SearchResult(Path(path), language, chunk_index, start_line, end_line, text, score))
        return tuple(sorted(results, key=lambda item: (-item.score, item.path.as_posix(), item.chunk_index))[:limit])

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
