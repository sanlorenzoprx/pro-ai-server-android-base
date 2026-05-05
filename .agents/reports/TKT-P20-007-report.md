# TKT-P20-007 Implementation Report

## Ticket

TKT-P20-007: Production Installer Docs and Smoke Script

## Summary

Added production installer smoke documentation, a reusable smoke script, troubleshooting updates, workflow updates, and Phase 20 closeout evidence.

## Changes

- Added `scripts/smoke-production-installer.ps1`.
- Updated release docs with production smoke paths and hardware smoke expectations.
- Updated troubleshooting docs for Termux readiness, USB tunnel failures, and test-prompt failures.
- Updated CLI workflow docs for `setup --production`, `installer-ui`, `test-prompt`, and smoke scripts.
- Added Phase 20 closeout report.
- Added docs tests for the production smoke path.

## Validation

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_docs.py
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\pro-ai-server.exe validate-release
.\.venv\Scripts\python.exe -m pytest
```

## Manual Evidence

No-phone smoke script is now available. Real hardware smoke remains a release prerequisite and should be recorded in `.agents/reports/phase-20-production-installer-hardening-report.md`.

## Follow-Up

Begin Phase 21 with `TKT-P21-001: Launch IDE readiness matrix`.

