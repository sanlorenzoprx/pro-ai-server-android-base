# TKT-P20-002 Implementation Report

## Ticket

TKT-P20-002: USB-First Exposure Guardrails

## Summary

Hardened the production installer path so USB remains the default and LAN/Tailscale require an explicit advanced-exposure opt-in.

## Changes

- Added production advanced-exposure gating in `plan_production_installer`.
- Added `setup --advanced-exposure` for production LAN/Tailscale opt-in.
- Added status exposure reporting so localhost/USB mode is visible in readiness output.
- Added tests that lock USB loopback binding for Termux scripts.
- Added tests that lock Continue USB config to `http://localhost:11434`.
- Added tests for production LAN/Tailscale rejection without explicit advanced exposure.

## Validation

```bash
.\.venv\Scripts\python.exe -m pytest tests/test_setup_workflow.py tests/test_termux_scripts.py tests/test_continue_config.py tests/test_status.py
.\.venv\Scripts\python.exe -m pytest tests/test_cli_workflows.py -k "production or status"
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\pro-ai-server.exe validate-release
.\.venv\Scripts\python.exe -m pytest
```

Results:

- Focused setup/Termux/Continue/status tests passed: 35 tests.
- Focused CLI production/status tests passed: 7 tests.
- Ruff passed.
- Release validation passed.
- Full suite passed: 355 tests.

## Follow-Up

- TKT-P20-003 should add the real Ollama `/api/generate` test prompt.
- TKT-P20-004 should expand production receipts with execution outcomes and richer error states.

