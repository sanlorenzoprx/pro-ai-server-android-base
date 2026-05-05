# Contract: Windows Release Candidate

## Phase

Phase 22: Production Hardware Validation and First Release Candidate

## Purpose

Validate the packaged Windows executable as the customer-facing release candidate artifact.

## Required Behavior

- Build the executable with `scripts/build-windows-exe.ps1`.
- Confirm bundled ADB runtime files are included.
- Run packaged no-phone smoke commands.
- Run packaged with-phone smoke commands when hardware is available.
- Record artifact path, build command, validation output, and known limitations.

## Validation

- `scripts/build-windows-exe.ps1`
- `dist/pro-ai-server/pro-ai-server.exe validate-release`
- `dist/pro-ai-server/pro-ai-server.exe setup --production`
- `dist/pro-ai-server/pro-ai-server.exe status`
- `dist/pro-ai-server/pro-ai-server.exe diagnose --output diagnostics.txt`
