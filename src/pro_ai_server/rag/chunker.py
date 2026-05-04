from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass


IGNORED_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "build",
    "dist",
    "node_modules",
}
TEXT_SUFFIXES = {
    ".md",
    ".py",
    ".toml",
    ".yml",
    ".yaml",
    ".json",
    ".txt",
    ".ps1",
    ".sh",
}


@dataclass(frozen=True)
class TextChunk:
    text: str
    start_line: int
    end_line: int


def should_index_file(path: Path) -> bool:
    if any(part in IGNORED_PARTS for part in path.parts):
        return False
    return path.suffix.lower() in TEXT_SUFFIXES


def chunk_text(text: str, *, max_words: int = 180, overlap_words: int = 30) -> tuple[str, ...]:
    words = text.split()
    if not words:
        return ()
    if max_words <= 0:
        raise ValueError("max_words must be greater than zero.")
    overlap = max(0, min(overlap_words, max_words - 1))
    step = max_words - overlap
    chunks = []
    for start in range(0, len(words), step):
        chunk = " ".join(words[start : start + max_words])
        if chunk:
            chunks.append(chunk)
        if start + max_words >= len(words):
            break
    return tuple(chunks)


def chunk_text_by_lines(text: str, *, max_lines: int = 80, overlap_lines: int = 10) -> tuple[TextChunk, ...]:
    lines = text.splitlines()
    if not lines:
        return ()
    if max_lines <= 0:
        raise ValueError("max_lines must be greater than zero.")
    overlap = max(0, min(overlap_lines, max_lines - 1))
    step = max_lines - overlap
    chunks: list[TextChunk] = []
    for start in range(0, len(lines), step):
        selected = lines[start : start + max_lines]
        if selected:
            chunks.append(TextChunk(text="\n".join(selected), start_line=start + 1, end_line=start + len(selected)))
        if start + max_lines >= len(lines):
            break
    return tuple(chunks)


def language_for_path(path: Path) -> str:
    return {
        ".py": "python",
        ".md": "markdown",
        ".toml": "toml",
        ".yml": "yaml",
        ".yaml": "yaml",
        ".json": "json",
        ".ps1": "powershell",
        ".sh": "shell",
    }.get(path.suffix.lower(), "text")
