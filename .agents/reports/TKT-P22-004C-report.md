# TKT-P22-004C Report

## Status

Completed.

## Summary

The packaged Windows executable completed live smoke against the Moto g 5G lightweight USB endpoint.

## Artifact

- `dist\pro-ai-server\pro-ai-server.exe`

## Device

- Phone: motorola moto g 5G (2022)
- Serial: `ZY22GKMWPN`
- Android: 13
- Compatibility lane: yellow/lightweight
- Endpoint: `http://localhost:11434` through `adb forward tcp:11434 tcp:11434`

## Validation

- `scripts/build-windows-exe.ps1`
  - passed
  - ran ruff, pytest, validate-release, packaged smoke, and PyInstaller build
- `dist\pro-ai-server\pro-ai-server.exe validate-release`
  - passed
- `dist\pro-ai-server\pro-ai-server.exe status`
  - phone connected
  - `adb forward tcp:11434` active
  - Ollama responding with 2 models
  - Continue ready in VS Code and Cursor
- `dist\pro-ai-server\pro-ai-server.exe server-check --profile lightweight`
  - detected `qwen2.5-coder:1.5b`
  - detected `qwen2.5-coder:0.5b`
- `dist\pro-ai-server\pro-ai-server.exe test-prompt --profile lightweight`
  - passed
  - response: `pro-ai-server-ready`

## Remaining Limitations

- First-run phone setup still required manual recovery during the Moto smoke:
  - temporary Android ADB install verifier change for Termux APK install
  - manual script staging because Android blocked direct ADB writes to Termux private home
  - Termux `apt update && apt full-upgrade -y` to repair stale `curl`/OpenSSL linkage
  - manual approval of Android background execution prompt

These limitations block a broad unattended installer claim, but do not block a narrow operator-assisted private beta.
