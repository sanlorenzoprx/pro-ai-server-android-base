# TKT-P20-002: USB-First Exposure Guardrails

## Target Repo

Pro AI Server

## Target Area

`src/pro_ai_server/setup_workflow.py`, `src/pro_ai_server/termux_scripts.py`, `src/pro_ai_server/continue_config.py`

## Phase

Phase 20: Production Installer Hardening

## Source Docs

- `.agents/phase-plans/phase-20-production-installer-hardening.md`
- `.agents/contracts/phase-20/usb-production-mode-contract.md`

## User / Operator Served

First-time customers who need the safest reliable setup path.

## Pain Solved

LAN and Tailscale are useful, but production onboarding should not lead customers into network exposure before USB is stable.

## Definition of Done

- Production install defaults to USB mode.
- LAN and Tailscale require explicit advanced flags or confirmation.
- USB scripts bind Ollama to `127.0.0.1:11434`.
- Continue config points to `http://localhost:11434` in USB mode.
- Receipt/status clearly reports USB tunnel state.
- Tests prevent accidental exposure regressions.

## Expected Files to Change

- `src/pro_ai_server/setup_workflow.py`
- `src/pro_ai_server/termux_scripts.py`
- `src/pro_ai_server/continue_config.py`
- `src/pro_ai_server/status.py`
- `tests/test_setup_workflow.py`
- `tests/test_termux_scripts.py`
- `tests/test_continue_config.py`
- `tests/test_status.py`

## Validation

- `ruff check .`
- `pytest tests/test_setup_workflow.py tests/test_termux_scripts.py tests/test_continue_config.py tests/test_status.py`
- `pro-ai-server validate-release`

## Dependencies

- TKT-P20-001

## Follow-Up Tickets Unlocked

- TKT-P20-003

