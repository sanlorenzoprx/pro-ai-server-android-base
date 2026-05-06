# TKT-P22-004C: Packaged Exe Live Smoke on Moto Lightweight Lane

## Target Repo

Pro AI Server and Pro Agentic Coding Server

## Target Area

Windows packaged release candidate smoke

## Phase

Phase 22: Production Hardware Validation and First Release Candidate

## Source Docs

- `.agents/contracts/phase-22/windows-rc-contract.md`
- `.agents/contracts/phase-22/release-evidence-contract.md`
- `docs/PRODUCTION_RC.md`

## User / Operator Served

Founder/operator validating the exact artifact a private beta customer would run.

## Pain Solved

Source-tree success is not enough. The packaged executable must prove it can see the phone endpoint, model inventory, and test prompt.

## Definition of Done

- `scripts/build-windows-exe.ps1` completes.
- `dist\pro-ai-server\pro-ai-server.exe validate-release` passes.
- `dist\pro-ai-server\pro-ai-server.exe status` reports phone, `adb forward`, Ollama, and IDE readiness.
- `dist\pro-ai-server\pro-ai-server.exe server-check --profile lightweight` passes.
- `dist\pro-ai-server\pro-ai-server.exe test-prompt --profile lightweight` returns `pro-ai-server-ready`.
- Results are recorded in a TKT-P22-004C report and summarized in `docs/PRODUCTION_RC.md`.

## Expected Files to Change

- `.agents/reports/TKT-P22-004C-report.md`
- `docs/PRODUCTION_RC.md`

## Validation

- `scripts/build-windows-exe.ps1`
- `dist\pro-ai-server\pro-ai-server.exe validate-release`
- `dist\pro-ai-server\pro-ai-server.exe status`
- `dist\pro-ai-server\pro-ai-server.exe server-check --profile lightweight`
- `dist\pro-ai-server\pro-ai-server.exe test-prompt --profile lightweight`

## Dependencies

- TKT-P22-004B

## Follow-Up Tickets Unlocked

- TKT-P22-005
