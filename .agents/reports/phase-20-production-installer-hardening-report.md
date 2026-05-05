# Phase 20 Production Installer Hardening Report

## Phase

Phase 20: Production Installer Hardening

## Summary

Phase 20 added the production installer foundation for Pro AI Server.

The product now has a production installer state machine, USB-first exposure guardrails, an Ollama `/api/generate` test prompt, support-ready setup receipts and error states, a reproducible Windows executable packaging path, a simple installer UI preview, and a production smoke script.

## Completed Tickets

- TKT-P20-001: Production installer state machine
- TKT-P20-002: USB-first exposure guardrails
- TKT-P20-003: End-to-end Ollama test prompt
- TKT-P20-004: Production receipts and error states
- TKT-P20-005: Windows executable packaging
- TKT-P20-006: Simple Windows installer UI
- TKT-P20-007: Production installer docs and smoke script

## Release Commands

No-phone production smoke:

```powershell
scripts/smoke-production-installer.ps1
```

Hardware production smoke:

```powershell
scripts/smoke-production-installer.ps1 -WithPhone
scripts/smoke-production-installer.ps1 -WithPhone -Serial <device-serial>
```

Windows executable build:

```powershell
scripts/build-windows-exe.ps1
```

## Validation Evidence

Automated validation for TKT-P20-007:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_docs.py
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\pro-ai-server.exe validate-release
.\.venv\Scripts\python.exe -m pytest
```

Manual hardware smoke evidence is still required before production release. Record:

- phone manufacturer/model
- Android version
- RAM and selected profile
- generated chat/autocomplete models
- Termux and Termux:API readiness
- USB tunnel result
- `server-check` result
- `test-prompt` result
- Continue config backup path if one was created
- any recoverable errors and recovery actions

## Production Posture

- USB is the default production path.
- LAN and Tailscale remain advanced exposure modes.
- Continue uses `http://localhost:11434` for USB mode.
- The first installer UI does not expose advanced network modes.
- Receipts and diagnostics are support-ready and redact user-profile paths.

## Follow-Up

Phase 21 can begin with `TKT-P21-001: Launch IDE readiness matrix`.

