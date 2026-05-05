# TKT-P21-001: Launch IDE Readiness Matrix

## Target Repo

Pro Agentic Coding Server

## Target Area

`src/pro_ai_server/ide.py`, launch docs

## Phase

Phase 21: DevStack Coding Server Launch

## Source Docs

- `.agents/phase-plans/phase-21-devstack-coding-server-launch.md`
- `.agents/contracts/phase-21/ide-readiness-contract.md`

## User / Operator Served

Developers setting up Cursor or VS Code with the local coding server.

## Pain Solved

Launch support needs a crisp IDE matrix so setup does not blur ready paths with later integrations.

## Definition of Done

- VS Code and Cursor are launch-supported.
- Windsurf and JetBrains are documented as follow-up.
- Detection output distinguishes missing IDE CLI, missing Continue extension, and ready state.
- Tests cover each launch IDE state.

## Expected Files to Change

- `src/pro_ai_server/ide.py`
- `src/pro_ai_server/cli.py`
- `docs/AGENT_WORKFLOWS.md`
- `tests/test_ide_detection.py`
- `tests/test_cli_workflows.py`

## Validation

- `ruff check .`
- `pytest tests/test_ide_detection.py tests/test_cli_workflows.py`

## Dependencies

- Phase 20 USB installer

## Follow-Up Tickets Unlocked

- TKT-P21-002

