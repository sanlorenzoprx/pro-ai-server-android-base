# TKT-P22-001C Implementation Report

## Ticket

TKT-P22-001C: Pinned APK Download and Checksum Verification

## Status

Completed.

## Summary

- Extended `pro-ai-server install-termux-apps` with pinned APK download support.
- Added URL plus SHA-256 options for F-Droid, Termux, and Termux:API.
- Refused downloads unless both URL and SHA-256 are provided.
- Verified downloaded APK SHA-256 before ADB install.
- Deleted downloaded APKs when checksum verification fails.
- Preserved `--yes` as the required confirmation gate for ADB APK installation.
- Updated CLI workflow, troubleshooting, and production RC docs.

## Files Changed

- `src/pro_ai_server/cli.py`
- `tests/test_cli_workflows.py`
- `tests/test_docs.py`
- `docs/CLI_WORKFLOW.md`
- `docs/TROUBLESHOOTING.md`
- `docs/PRODUCTION_RC.md`
- `.agents/reports/TKT-P22-001C-report.md`

## Validation

- `.\\.venv\\Scripts\\python.exe -m pytest tests/test_cli_workflows.py tests/test_docs.py`
  - 91 passed
- `.\\.venv\\Scripts\\python.exe -m ruff check src/pro_ai_server/cli.py tests/test_cli_workflows.py tests/test_docs.py`
  - Passed
- `.\\.venv\\Scripts\\pro-ai-server.exe validate-release`
  - Passed
- `.\\.venv\\Scripts\\python.exe -m pytest`
  - 400 passed

## Follow-Up

- Add an official pinned APK manifest once product chooses exact F-Droid, Termux, and Termux:API release versions and checksums.
