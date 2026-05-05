# TKT-P22-001F: Pinned APK Manifest and Cross-Lane Validation Matrix

## Target Repo

Pro AI Server

## Target Area

Android APK manifest completion and hardware validation lanes

## Phase

Phase 22: Production Hardware Validation and First Release Candidate

## Source Docs

- `.agents/phase-plans/phase-22-production-hardware-validation-rc.md`
- `.agents/contracts/phase-22/android-compatibility-contract.md`

## User / Operator Served

Production operator who needs trusted APK inputs without guessing versions or claiming unsupported phones.

## Pain Solved

The APK manifest cannot pin "latest" or leave `TBD` placeholders. It needs reviewed stable APK URLs and SHA-256 values plus a validation matrix that separates Android 7-9, Android 10-13, and Android 14/15 behavior.

## Definition of Done

- Bundled APK manifest has reviewed F-Droid, Termux, and Termux:API entries with URL, version, version code, Android range, and SHA-256.
- CLI can render the APK manifest and Android validation matrix.
- `setup --production --execute --yes` can use the bundled manifest with `--use-pinned-apk-manifest`.
- Docs record Android 7-9, 10-13, and 14/15 validation lanes.
- Tests prove the manifest has no placeholders and selects Android 7+ entries.

## Expected Files to Change

- `src/pro_ai_server/android_compatibility.py`
- `src/pro_ai_server/android-apk-manifest.json`
- `src/pro_ai_server/cli.py`
- `pyproject.toml`
- `tests/test_android_compatibility.py`
- `tests/test_cli_workflows.py`
- `tests/test_docs.py`
- `docs/ANDROID_COMPATIBILITY.md`
- `docs/CLI_WORKFLOW.md`
- `docs/TROUBLESHOOTING.md`
- `docs/PRODUCTION_RC.md`
- `.agents/reports/TKT-P22-001F-report.md`

## Validation

- `pytest tests/test_android_compatibility.py tests/test_cli_workflows.py tests/test_docs.py`
- `ruff check .`
- `pro-ai-server apk-manifest --android-version 13`
- `pro-ai-server android-validation-matrix`
- Live current device: `pro-ai-server android-compatibility --serial ZY22GKMWPN`

## Dependencies

- TKT-P22-001D

## Follow-Up Tickets Unlocked

- Cross-device hardware smoke for Android 7-9 and Android 14/15.
