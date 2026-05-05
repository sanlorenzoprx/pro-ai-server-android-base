# TKT-P22-002 Implementation Report

## Ticket

TKT-P22-002: Packaged Windows Exe Release-Candidate Smoke

## Status

Completed.

## Summary

- Built the Windows release-candidate artifact at `dist\pro-ai-server\pro-ai-server.exe`.
- Fixed the PyInstaller entrypoint so the package builds from a generated script instead of passing `-m pro_ai_server.cli` to PyInstaller.
- Fixed bundled Platform Tools packaging by resolving the source `embedded-tools\windows\platform-tools` directory to an absolute path before `--add-data`.
- Changed the no-phone production smoke command to use `--profile lightweight` so the packaged smoke remains deterministic without requiring a connected phone.
- Verified bundled ADB resolution from inside the packaged executable.

## Files Changed

- `scripts/build-windows-exe.ps1`
- `src/pro_ai_server/packaging.py`
- `tests/test_packaging.py`
- `docs/PRODUCTION_RC.md`
- `.agents/reports/TKT-P22-002-report.md`

## Validation

- `.\\scripts\\build-windows-exe.ps1`
  - Passed.
  - Ran `ruff check .`: passed.
  - Ran full pytest suite: 413 passed.
  - Ran source `validate-release`: passed.
  - Built `dist\pro-ai-server\pro-ai-server.exe` with PyInstaller 6.20.0.
- `dist\\pro-ai-server\\pro-ai-server.exe validate-platform-tools --root .`
  - Passed for source and packaged ADB layouts.
- `dist\\pro-ai-server\\pro-ai-server.exe doctor`
  - Passed bundled ADB discovery.
  - Detected VS Code and Cursor with Continue installed.
- `dist\\pro-ai-server\\pro-ai-server.exe setup --production --profile lightweight`
  - Passed as plan-only no-phone smoke.
  - Produced the 13-step production installer plan with the lightweight model profile.
- `dist\\pro-ai-server\\pro-ai-server.exe status`
  - Passed command execution.
  - Detected phone `ZY22GKMWPN`.
  - Reported USB tunnel inactive and Ollama unavailable, which matches the current live hardware state.
- `dist\\pro-ai-server\\pro-ai-server.exe diagnose --output diagnostics.txt`
  - Passed command execution.
  - Confirmed packaged ADB path under `dist\pro-ai-server\_internal`.
  - Confirmed Moto g 5G (2022), Android 13, arm64-v8a, 5.54 GB RAM, and 125.27 GB free storage.

## Hardware Evidence

- Connected phone: `ZY22GKMWPN`
- Device: motorola moto g 5G (2022)
- Android: 13
- ABI: arm64-v8a
- RAM: 5.54 GB
- Storage free: 125.27 GB
- Current with-phone packaged smoke status: partial pass.
- Blocked items: no active `adb reverse` tunnel and no reachable Ollama endpoint at `localhost:11434`.

## Known Limitations

- The packaged executable is validated as an RC artifact, but the current phone still needs Termux, Termux:API, Ollama, selected models, and a live USB tunnel before full customer-promise smoke can pass.
- The build script writes a transient `diagnostics.txt` during smoke; this is evidence scratch output and is not part of the release artifact.

## Follow-Up

- Continue with TKT-P22-003 for live Continue IDE validation after the phone server path is running.
