# TKT-P22-001F Implementation Report

## Ticket

TKT-P22-001F: Pinned APK Manifest and Cross-Lane Validation Matrix

## Status

Implemented in source; live Android 7-9 and Android 14/15 devices are still needed for full cross-lane hardware proof.

## Summary

- Added bundled APK manifest at `src/pro_ai_server/android-apk-manifest.json`.
- Manifest pins reviewed Android 7+ F-Droid lane artifacts:
  - F-Droid client `1.23.1` / version code `1023051`
  - Termux `0.118.3` / version code `1002`
  - Termux:API `0.53.0` / version code `1002`
- Added manifest loading, rendering, Android-range selection, and setup flag generation.
- Added Android validation lanes for:
  - Android 7-9 yellow
  - Android 10-13 green
  - Android 14-15 green
- Added CLI commands:
  - `pro-ai-server apk-manifest --android-version <version>`
  - `pro-ai-server android-validation-matrix`
- Added `setup --production --execute --yes --use-pinned-apk-manifest` so production setup can use the bundled manifest instead of manually supplied APK URLs/checksums.
- Updated docs and RC evidence with cross-lane validation status.

## Source Review

- Termux F-Droid page lists stable suggested Termux `0.118.3` and states it requires Android 7.0 or newer.
- F-Droid package API returned Termux suggested version code `1002`, Termux:API suggested version code `1002`, and F-Droid client suggested version code `1023052`.
- F-Droid verification reports published signed APK SHA-256 values for the pinned artifacts.
- F-Droid client was pinned to `1.23.1` because it had reviewed checksum evidence at implementation time; `1.23.2` should be considered only after manifest review.

## Files Changed

- `.agents/phase-plans/phase-22-production-hardware-validation-rc.md`
- `.agents/build-tickets/phase-22/TKT-P22-001F-pinned-apk-manifest-cross-lane-validation.md`
- `pyproject.toml`
- `src/pro_ai_server/android_compatibility.py`
- `src/pro_ai_server/android-apk-manifest.json`
- `src/pro_ai_server/cli.py`
- `tests/test_android_compatibility.py`
- `tests/test_cli_workflows.py`
- `tests/test_docs.py`
- `docs/ANDROID_COMPATIBILITY.md`
- `docs/CLI_WORKFLOW.md`
- `docs/TROUBLESHOOTING.md`
- `docs/PRODUCTION_RC.md`
- `.agents/reports/TKT-P22-001F-report.md`

## Validation

- `.\\.venv\\Scripts\\python.exe -m pytest tests/test_android_compatibility.py tests/test_cli_workflows.py tests/test_docs.py -q`
  - 110 passed
- `.\\.venv\\Scripts\\pro-ai-server.exe apk-manifest --android-version 13`
  - Printed F-Droid Client `1.23.1`, Termux `0.118.3`, Termux:API `0.53.0`, URLs, SHA-256 values, and setup flags.
- `.\\.venv\\Scripts\\pro-ai-server.exe android-validation-matrix`
  - Printed Android 7-9, 10-13, and 14-15 validation lanes.
- `.\\.venv\\Scripts\\pro-ai-server.exe android-compatibility --serial ZY22GKMWPN`
  - Passed; Moto g 5G Android 13, arm64-v8a, 5.54 GB RAM, yellow/lightweight.
- `.\\.venv\\Scripts\\python.exe -m ruff check .`
  - Passed
- `.\\.venv\\Scripts\\pro-ai-server.exe validate-release`
  - Passed
- `.\\.venv\\Scripts\\python.exe -m pytest`
  - 422 passed

## Live Hardware Evidence

- Current live device remains Moto g 5G (2022), Android 13, arm64-v8a, 5.54 GB RAM.
- Lane: Android 10-13.
- Model tier remains yellow/lightweight because RAM is under 6 GB.
- Android 7-9 and Android 14/15 live devices are still required before claiming those lanes as hardware-validated.
