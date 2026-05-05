# TKT-P21-002: Continue.dev Coding Config Presets

## Target Repo

Pro Agentic Coding Server

## Target Area

`src/pro_ai_server/continue_config.py`

## Phase

Phase 21: DevStack Coding Server Launch

## Source Docs

- `.agents/phase-plans/phase-21-devstack-coding-server-launch.md`
- `.agents/contracts/phase-21/continue-devstack-config-contract.md`

## User / Operator Served

Developers using Continue with Cursor or VS Code.

## Pain Solved

The DevStack launch needs reliable chat and autocomplete presets tied to the detected phone profile.

## Definition of Done

- Continue config uses hardware-selected chat and autocomplete models.
- USB endpoint is the launch default.
- Existing config backup/restore instructions remain clear.
- CLI output tells the user which IDEs can use the config.
- Tests cover config rendering and backup behavior.

## Expected Files to Change

- `src/pro_ai_server/continue_config.py`
- `src/pro_ai_server/cli.py`
- `docs/AGENT_WORKFLOWS.md`
- `tests/test_continue_config.py`
- `tests/test_cli_workflows.py`

## Validation

- `ruff check .`
- `pytest tests/test_continue_config.py tests/test_cli_workflows.py`

## Dependencies

- TKT-P21-001

## Follow-Up Tickets Unlocked

- TKT-P21-003

