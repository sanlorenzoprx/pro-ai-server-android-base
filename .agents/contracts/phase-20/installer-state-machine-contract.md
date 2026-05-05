# Contract: Production Installer State Machine

## Phase

Phase 20: Production Installer Hardening

## Purpose

Provide one production setup path that can be used by the CLI, Windows executable, and later UI wrapper.

## Required Steps

- host checks
- Android phone detection
- ADB verification
- hardware scan
- model profile selection
- Termux readiness
- script generation
- script push
- server start instructions or trigger
- USB tunnel creation
- model inventory check
- test prompt
- final receipt

## Behavior

- Steps must be idempotent where practical.
- Each step must return success, warning, or failure state.
- Failures must include a user-facing message and support/debug detail.
- Existing CLI setup behavior should be reused rather than duplicated.
- The default profile should come from hardware scan unless explicitly overridden.

## Validation

- Unit tests cover step ordering and failure mapping.
- CLI tests cover the production install command or production setup mode.
- Manual smoke uses a USB-connected Android phone.

