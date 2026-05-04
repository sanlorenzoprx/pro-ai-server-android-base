from __future__ import annotations

import subprocess
from collections.abc import Callable
from pathlib import Path


CommandRunner = Callable[[list[str]], str]


def default_command_runner(command: list[str]) -> str:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        return result.stderr.strip() or result.stdout.strip() or "unavailable"
    return result.stdout.strip()


def build_prime_report(
    *,
    command_runner: CommandRunner = default_command_runner,
    index_file_count: int | None = None,
    index_chunk_count: int | None = None,
) -> str:
    branch = command_runner(["git", "branch", "--show-current"]) or "unknown"
    status = command_runner(["git", "status", "--short"]) or "clean"
    recent = command_runner(["git", "log", "--oneline", "-n", "20"]) or "none"
    diff_stat = command_runner(["git", "diff", "--stat"]) or "none"
    index_files = "unknown" if index_file_count is None else str(index_file_count)
    index_chunks = "unknown" if index_chunk_count is None else str(index_chunk_count)

    return "\n".join(
        [
            "# Agent Prime",
            "",
            "## Git",
            "",
            f"Branch: {branch}",
            "",
            "### Status",
            "",
            _fenced(status),
            "",
            "### Recent Commits",
            "",
            _fenced(recent),
            "",
            "### Diff Stat",
            "",
            _fenced(diff_stat),
            "",
            "## Index",
            "",
            f"Indexed files: {index_files}",
            f"Indexed chunks: {index_chunks}",
            "",
            "## Validation",
            "",
            "```bash",
            "ruff check .",
            "pytest",
            "pro-ai-server validate-release",
            "```",
            "",
            "## Risks",
            "",
            "- Check dirty worktree before editing.",
            "- Re-index before relying on context for implementation.",
            "",
        ]
    )


def write_prime_report(report: str, *, root: Path = Path(".")) -> Path:
    path = root / ".agents" / "memory" / "last-prime.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report, encoding="utf-8")
    return path


def _fenced(value: str) -> str:
    return f"```text\n{value}\n```"

