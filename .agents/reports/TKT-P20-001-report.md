# TKT-P20-001 Implementation Report

## Ticket

TKT-P20-001: Production Installer State Machine

## Summary

Added the first production installer state-machine layer for Pro AI Server.

The new production plan is pure and structured, so the CLI, packaged executable, and future UI can share the same step model. It reuses the existing setup workflow for model selection, Termux script planning, Continue config planning, USB tunnel planning, and script push planning.

## Changes

- Added `ProductionInstallerStep` and `ProductionInstallerPlan`.
- Added `plan_production_installer`.
- Added `mark_production_step_failed` for structured failure mapping.
- Added `setup --production` CLI output for the production state-machine plan.
- Extended setup receipts with optional production installer step rendering.
- Added tests for required step order, setup workflow reuse, failure mapping, receipt rendering, and CLI output.

## Validation

```bash
.\.venv\Scripts\python.exe -m pytest tests/test_setup_workflow.py tests/test_setup_receipt.py tests/test_cli_workflows.py
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\pro-ai-server.exe validate-release
.\.venv\Scripts\python.exe -m pytest
```

Results:

- 80 focused tests passed.
- Ruff passed.
- Release validation passed.
- Full suite passed: 348 tests.

## Follow-Up

- TKT-P20-002 should harden USB-first exposure rules.
- TKT-P20-003 should replace the test-prompt placeholder with a real Ollama `/api/generate` check.
- TKT-P20-004 should expand receipts and error states with production execution outcomes.

