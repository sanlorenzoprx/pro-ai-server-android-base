# Contract: USB Production Mode

## Phase

Phase 20: Production Installer Hardening

## Purpose

Make USB the production default for Pro AI Server.

## Required Behavior

- USB mode binds the phone-side Ollama server to `127.0.0.1:11434`.
- Windows reaches the server through `adb reverse tcp:11434 tcp:11434`.
- Continue-compatible IDEs use `http://localhost:11434`.
- LAN and Tailscale are advanced modes and require explicit flags.
- Installer UI should not present LAN or Tailscale as first-run choices.

## Safety Rules

- Do not bind Ollama to `0.0.0.0` unless the operator explicitly chooses an advanced mode.
- Warn before any mode that exposes the server outside phone-local loopback.
- Final receipt must show which exposure mode is active.

## Validation

- Tests assert USB defaults.
- Tests assert LAN/Tailscale require explicit host or confirmation.
- Status output reports active USB tunnel state.

