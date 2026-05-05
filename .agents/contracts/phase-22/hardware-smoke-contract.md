# Contract: Production Hardware Smoke

## Phase

Phase 22: Production Hardware Validation and First Release Candidate

## Purpose

Validate the USB-first installer path on real Android hardware before release-candidate promotion.

## Required Behavior

- Record phone model, Android version, RAM profile, and detected serial.
- Verify ADB detection and USB debugging authorization.
- Run production setup planning and execution.
- Verify Termux readiness, script push, USB tunnel, server status, model inventory, and test prompt.
- Record selected chat and autocomplete models.
- Record every failure and recovery step.

## Validation

- `scripts/smoke-production-installer.ps1 -WithPhone`
- `pro-ai-server setup --execute --yes`
- `pro-ai-server tunnel`
- `pro-ai-server test-prompt`
- `pro-ai-server status`
