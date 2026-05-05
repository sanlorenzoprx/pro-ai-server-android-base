# TKT-P20-007: Production Installer Docs and Smoke Script

## Target Repo

Pro AI Server

## Target Area

Release docs, troubleshooting docs, smoke checklist

## Phase

Phase 20: Production Installer Hardening

## Source Docs

- `.agents/phase-plans/phase-20-production-installer-hardening.md`
- All Phase 20 contracts

## User / Operator Served

Customers, support, and release operators.

## Pain Solved

Production release needs a repeatable smoke script and customer-safe docs before promotion.

## Definition of Done

- Docs explain USB debugging, Termux, Termux:API, Ollama, USB tunnel, model profiles, Continue config, and common failures.
- Smoke checklist covers fresh install, repeat install, missing phone, unauthorized phone, missing Termux, tunnel failure, and test prompt failure.
- Release docs identify artifact location and validation commands.
- Phase 20 implementation report records manual evidence.

## Expected Files to Change

- `docs/RELEASE.md`
- `docs/TROUBLESHOOTING.md`
- `docs/CLI_WORKFLOW.md`
- `.agents/reports/phase-20-production-installer-hardening-report.md`

## Validation

- `ruff check .`
- `pytest tests/test_docs.py`
- `pro-ai-server validate-release`

## Dependencies

- TKT-P20-001 through TKT-P20-006

## Follow-Up Tickets Unlocked

- TKT-P21-001

