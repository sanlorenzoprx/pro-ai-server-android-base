# TKT-P20-004: Production Receipts and Error States

## Target Repo

Pro AI Server

## Target Area

`src/pro_ai_server/setup_receipt.py`, `src/pro_ai_server/diagnostics.py`

## Phase

Phase 20: Production Installer Hardening

## Source Docs

- `.agents/phase-plans/phase-20-production-installer-hardening.md`
- `.agents/contracts/phase-20/installer-receipt-error-contract.md`

## User / Operator Served

Customers, support operators, and future installer UI users.

## Pain Solved

Production installs need clear "what happened, what is next, what failed" reporting instead of raw command output.

## Definition of Done

- Setup receipt includes device, model profile, connection mode, generated/pushed files, config backup, tunnel, server, and test prompt result.
- Error states include problem, likely cause, recovery action, and debug detail.
- Diagnostics can include receipt context without leaking secrets.
- Rendered output is deterministic and readable.
- Tests cover success, partial success, and failure receipts.

## Expected Files to Change

- `src/pro_ai_server/setup_receipt.py`
- `src/pro_ai_server/diagnostics.py`
- `src/pro_ai_server/cli.py`
- `tests/test_setup_receipt.py`
- `tests/test_diagnostics.py`
- `tests/test_cli_workflows.py`

## Validation

- `ruff check .`
- `pytest tests/test_setup_receipt.py tests/test_diagnostics.py tests/test_cli_workflows.py`
- `pro-ai-server validate-release`

## Dependencies

- TKT-P20-001
- TKT-P20-003

## Follow-Up Tickets Unlocked

- TKT-P20-005
- TKT-P20-006

