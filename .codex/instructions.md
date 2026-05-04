# Codex Instructions for Pro AI Server

You are working on Pro AI Server.

Pro AI Server turns an Android phone into a local AI coding server and is evolving into an agentic local code assistant.

## Core Rules

- Preserve existing CLI behavior.
- Prefer small modules.
- Add tests for new behavior.
- Validate after every meaningful change.
- Do not skip `ruff check .`, `pytest`, and `pro-ai-server validate-release`.
- Write plans before implementation.
- Write reports after implementation.
- Improve rules after mistakes.
- Treat `.agents/`, `.codex/`, and `.cursor/` as the AI layer second codebase.
- Use the CodeFlow Build Bridge for major work: phase plan -> build tickets -> contracts -> implementation -> validation evidence -> closeout.
- Do not start major runtime work unless a matching `.agents/build-tickets/` ticket exists.

## Current Stack

- Python 3.11+
- Typer CLI
- Rich console output
- PyYAML
- pytest
- Ruff

## Default Validation

```bash
ruff check .
pytest
pro-ai-server validate-release
```

## Architecture Direction

Build in phases:

1. AI layer
2. CodeFlow Build Bridge
3. local gateway
4. Ollama proxy
5. model router
6. codebase index/RAG
7. agent planner
8. agent implementer
9. validation/reporting
10. self-improvement loop
11. GitHub issue-to-PR workflow
