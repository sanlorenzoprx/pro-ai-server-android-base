# Release Checklist

This checklist is Windows-first and assumes PowerShell from the repository root after installing the project in editable mode:

```powershell
python -m pip install -e ".[dev]"
```

## Required Gates

Run these before tagging, packaging, or handing off a release build:

```powershell
pro-ai-server validate-release
pro-ai-server validate-platform-tools
pytest
ruff check .
pro-ai-server doctor
```

`validate-release` checks the bundled ADB runtime files, embedded tool package data, and CI gate coverage. `validate-platform-tools` is the narrower Windows Platform Tools check for the bundled ADB layout.

CI also runs `pro-ai-server validate-release` and a lightweight wheel build:

```powershell
python -m pip wheel . --no-deps --wheel-dir dist
```

The wheel command uses pip and the existing `pyproject.toml` build backend, so it does not add a new release dependency.

## Windows Executable Build

Build the customer-facing Windows executable from PowerShell:

```powershell
scripts/build-windows-exe.ps1
```

The script installs the project with dev dependencies, runs lint and tests, validates release readiness, then builds the executable with PyInstaller.

Expected artifact:

```powershell
dist\pro-ai-server\pro-ai-server.exe
```

The packaging script includes the bundled ADB runtime data and excludes development-only modules such as `pytest` and `ruff`. It also avoids packaging local caches, virtualenvs, `.env` files, and build output directories.

After building, the script smokes these packaged commands:

```powershell
dist\pro-ai-server\pro-ai-server.exe validate-platform-tools --root .
dist\pro-ai-server\pro-ai-server.exe doctor
dist\pro-ai-server\pro-ai-server.exe setup --production
dist\pro-ai-server\pro-ai-server.exe status
dist\pro-ai-server\pro-ai-server.exe diagnose --output diagnostics.txt
```

## Bundled Platform Tools

Release builds include these Windows ADB files:

- `embedded-tools/windows/platform-tools/adb.exe`
- `embedded-tools/windows/platform-tools/AdbWinApi.dll`
- `embedded-tools/windows/platform-tools/AdbWinUsbApi.dll`

Fastboot is not used by the MVP workflow, and release validation does not require `fastboot.exe`.

## Refresh Platform Tools

Preferred refresh path:

```powershell
scripts/download-platform-tools.ps1
pro-ai-server validate-platform-tools
```

Fallback path when the script cannot download Platform Tools:

1. Install or update Android Studio.
2. Open SDK Manager and install Android SDK Platform-Tools.
3. Copy `adb.exe`, `AdbWinApi.dll`, and `AdbWinUsbApi.dll` from the SDK `platform-tools` directory into `embedded-tools/windows/platform-tools`.
4. Run `pro-ai-server validate-platform-tools`.

Do not add `fastboot.exe` as a release requirement unless the product flow starts using fastboot.

## Smoke Commands

After the required gates pass, run the smoke path that exercises script generation, setup planning, and diagnostics without requiring a phone mutation:

```powershell
pro-ai-server generate-scripts --mode usb
pro-ai-server setup --production
pro-ai-server installer-ui
pro-ai-server installer-ui --mock-failure termux-readiness
pro-ai-server diagnose --output diagnostics.txt
```

Use `setup --production` without `--execute` for release smoke checks so it prints the production state machine without writing Continue config, pushing files, or creating an ADB tunnel.

The scripted no-phone smoke path is:

```powershell
scripts/smoke-production-installer.ps1
```

For hardware smoke with a connected Android phone:

```powershell
scripts/smoke-production-installer.ps1 -WithPhone
scripts/smoke-production-installer.ps1 -WithPhone -Serial <device-serial>
```

Hardware smoke covers fresh install, repeat install, Termux readiness, USB tunnel creation, Continue config, model inventory, test prompt, status, and diagnostics. Record the phone model, Android version, RAM profile, selected models, and any manual Termux/Ollama steps in the Phase 20 closeout report.
