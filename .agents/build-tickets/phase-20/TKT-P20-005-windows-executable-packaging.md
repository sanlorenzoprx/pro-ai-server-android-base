# TKT-P20-005: Windows Executable Packaging

## Target Repo

Pro AI Server

## Target Area

Packaging scripts and release docs

## Phase

Phase 20: Production Installer Hardening

## Source Docs

- `.agents/phase-plans/phase-20-production-installer-hardening.md`
- `.agents/contracts/phase-20/windows-packaging-contract.md`

## User / Operator Served

Non-developer Windows customers.

## Pain Solved

Customers should not need Python, pip, or editable installs to run the product.

## Definition of Done

- Add a reproducible Windows packaging command.
- Packaged artifact runs `doctor`, `setup`, `status`, `diagnose`, and `validate-platform-tools`.
- Bundled ADB resolution works from packaged layout.
- Build excludes local caches, virtualenvs, and secrets.
- Release docs include packaging and smoke steps.

## Expected Files to Change

- `scripts/`
- `docs/RELEASE.md`
- `src/pro_ai_server/cli.py`
- `src/pro_ai_server/release_validation.py`
- `tests/test_release_validation.py`
- `tests/test_packaging.py`

## Validation

- `ruff check .`
- `pytest tests/test_packaging.py tests/test_release_validation.py`
- Manual smoke: run the built `.exe` on Windows

## Dependencies

- TKT-P20-001 through TKT-P20-004

## Follow-Up Tickets Unlocked

- TKT-P20-006
- TKT-P20-007

