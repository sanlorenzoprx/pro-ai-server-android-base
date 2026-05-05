# Production Release Candidate

Phase 22 validates the first production release candidate on real hardware before private beta, creator traffic, affiliate traffic, or paid launch.

The release-candidate path is intentionally narrow:

- Windows first.
- USB-first Android phone connection.
- Local Ollama-compatible endpoint at `http://localhost:11434`.
- VS Code or Cursor through Continue.
- No LAN, Tailscale, JetBrains, or Windsurf as release blockers.

## Required Gates

Run source-tree gates before building the packaged artifact:

```powershell
pro-ai-server validate-release
pytest
ruff check .
```

Build and smoke the Windows release candidate:

```powershell
scripts/build-windows-exe.ps1
dist\pro-ai-server\pro-ai-server.exe validate-release
dist\pro-ai-server\pro-ai-server.exe setup --production
dist\pro-ai-server\pro-ai-server.exe status
dist\pro-ai-server\pro-ai-server.exe diagnose --output diagnostics.txt
```

Run real hardware smoke with a connected Android phone:

```powershell
scripts/smoke-production-installer.ps1 -WithPhone
pro-ai-server setup --execute --yes
pro-ai-server install-termux-apps --serial ZY22GKMWPN
pro-ai-server tunnel
pro-ai-server test-prompt
pro-ai-server status
```

Run DevStack IDE validation:

```powershell
pro-ai-server devstack-ide-status
pro-ai-server configure-devstack
```

Then confirm Continue chat and one coding assistance moment inside VS Code or Cursor.

## Hardware Smoke Matrix

Record one row per phone:

Use status values `completed`, `blocked`, or `skipped`. Do not leave a check blank.

| Phone | Android | Serial Recorded | RAM Profile | Chat Model | Autocomplete Model | ADB Authorized | Setup Execute | Termux Ready | Scripts Pushed | Tunnel | Model Inventory | Test Prompt | Status | Result |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| motorola moto g 5G (2022) | 13 | ZY22GKMWPN | professional | qwen2.5-coder:3b | qwen2.5-coder:1.5b-base | completed | skipped | blocked | blocked | completed | blocked | blocked | blocked | Termux/Ollama not installed yet |

Device identity record:

- Phone model:
- Android version:
- Detected serial:
- USB debugging authorization: `completed`, `blocked`, or `skipped`
- RAM profile:
- Selected chat model:
- Selected autocomplete model:
- Operator:
- Date:

Run checklist:

| Step | Command Or Evidence | Expected Result | Status | Notes |
|---|---|---|---|---|
| ADB detection | `pro-ai-server scan --serial <serial>` | Phone is detected and authorized | completed | ZY22GKMWPN detected |
| Production plan | `pro-ai-server setup --production` | USB-first production plan renders | completed | 13-step professional profile plan rendered |
| Production execute | `pro-ai-server setup --execute --yes --serial <serial>` | Setup completes or records recoverable failure | blocked | TBD |
| Termux readiness | `pro-ai-server termux-check --serial <serial>` | Termux, Termux:API, and home state are ready | blocked | Termux and Termux:API not installed; Termux home not initialized |
| Script push | `pro-ai-server push-scripts --serial <serial>` | Termux scripts are delivered | blocked | `/data/data/com.termux` permission denied because Termux is unavailable |
| USB tunnel | `pro-ai-server tunnel --serial <serial>` | `adb reverse tcp:11434 tcp:11434` is active | completed | Port 11434 reverse requested successfully |
| Server status | `pro-ai-server status` | Local server readiness is visible | blocked | Phone and tunnel OK; Ollama localhost:11434 not reachable |
| Model inventory | `pro-ai-server server-check` | Required model inventory is visible | blocked | Ollama localhost:11434 not reachable |
| Test prompt | `pro-ai-server test-prompt` | Local model returns a valid response | blocked | Ollama localhost:11434 not reachable |

Evidence log:

| Evidence | Filename Or Command Output Summary | Status | Notes |
|---|---|---|---|
| Phone photo | TBD | blocked | Show USB-connected Android phone |
| Terminal smoke output | TKT-P22-001 report | completed | Scan, plan, Termux check, tunnel, status, server-check, and test-prompt summarized |
| Test prompt response | TBD | blocked | Record prompt and short response summary |
| Diagnostics file | `diagnostics.txt` | blocked | Attach when generated |

Failure notes:

- Record missing phone, unauthorized phone, missing Termux, missing Ollama, tunnel failure, model pull failure, slow response, and test prompt failure.
- Record recovery steps and whether the issue blocks release.
- Keep blocked checks marked `blocked` until the exact recovery is verified.
- Mark unavailable checks `skipped` only when the reason is intentional and non-blocking.

Recovery log:

| Failure | Recovery Attempted | Result | Blocks RC |
|---|---|---|---|
| ADB did not initially see phone | Unlocked phone, restarted ADB, rescanned | Resolved; device detected as ZY22GKMWPN | No |
| `df /data` mounted at `/storage/emulated/0/Android/obb` | Updated storage parser to accept single-row Android storage mount output | Resolved; scan reports 125.54 GB free | No |
| Termux missing | Added `install-termux-apps`; F-Droid is installed and the command opens Termux and Termux:API package pages or installs supplied APKs with `--yes` | Blocked until Termux and Termux:API are installed and opened once | Yes |
| Ollama unavailable | Ran `status`, `server-check`, and `test-prompt` after USB tunnel | Blocked until phone-side Ollama server is installed and running | Yes |

## Hardware Smoke Attempts

### 2026-05-05: Initial Android Detection Attempt

Status: `blocked`

Evidence:

- `pro-ai-server doctor` passed bundled ADB, Python, VS Code, Cursor, and Continue extension checks.
- `adb devices -l` from bundled ADB returned no attached devices.
- `pro-ai-server scan` returned "No ADB devices found."
- Windows present-device scan did not show an Android, ADB, MTP, Portable, Samsung, Pixel, Motorola, OnePlus, Xiaomi, or Phone device.
- ADB server restart completed, but the device list still showed no attached devices.

Likely recovery paths:

- Unlock phone and accept any USB debugging prompt.
- Confirm USB debugging is enabled in Developer Options.
- Use a known data-capable USB cable and a direct USB port.
- Set the phone USB mode to file transfer or USB debugging when prompted.
- If using Remote Desktop, confirm USB device redirection passes the phone to this Windows session.
- Install or refresh the OEM Android USB driver if Windows still does not show the phone.

Release impact: blocks hardware smoke until ADB can see the phone.

### 2026-05-05: Moto g 5G Hardware Smoke Attempt

Status: `blocked`

Device identity:

- Phone model: motorola moto g 5G (2022)
- Android version: 13
- Detected serial: ZY22GKMWPN
- ABI: arm64-v8a
- RAM profile: professional
- RAM: 5.54 GB
- Free storage: 125.54 GB
- Battery: 68%
- Charging: true
- Selected chat model: qwen2.5-coder:3b
- Selected autocomplete model: qwen2.5-coder:1.5b-base

Completed:

- ADB detection.
- Hardware scan.
- Production setup plan.
- USB reverse tunnel on port 11434.
- F-Droid package pages opened with `pro-ai-server install-termux-apps --serial ZY22GKMWPN`.
- VS Code and Cursor Continue readiness through `pro-ai-server doctor`.

Blocked:

- Termux readiness: Termux, Termux:API, and initialized Termux home are missing.
- Script push: `/data/data/com.termux` permission denied because Termux is unavailable.
- Model inventory: Ollama endpoint at `http://localhost:11434` is not reachable.
- Test prompt: Ollama endpoint at `http://localhost:11434` is not reachable.

Release impact: blocks full hardware smoke until Termux, Termux:API, Ollama, and selected models are installed on the phone.

Automation note: use `pro-ai-server install-termux-apps --serial ZY22GKMWPN` to open the F-Droid "Install unknown apps" permission screen plus the required Termux package pages. If F-Droid is not present, provide a reviewed local APK with `--fdroid-apk` and `--yes`, or provide a pinned download with `--fdroid-url`, `--fdroid-sha256`, and `--yes`. For a full ADB install path, provide reviewed local APKs or pinned URL/SHA-256 pairs for F-Droid, Termux, and Termux:API.

## Packaged Exe Evidence

Record:

- Artifact path: `dist\pro-ai-server\pro-ai-server.exe`
- Build command and result.
- `validate-release` result.
- No-phone smoke result.
- With-phone smoke result when available.
- Bundled ADB validation result.
- Known packaging limitations.

## Live IDE Evidence

Record:

- IDE: VS Code or Cursor.
- Continue extension state.
- API base: `http://localhost:11434`.
- Chat prompt used.
- Response summary.
- Autocomplete or coding assistance proof.
- Latency or low-RAM caveats.
- Screenshot or recording filename when available.

## Release Evidence Bundle

The final evidence bundle should include:

- Hardware smoke matrix.
- Packaged exe smoke results.
- Live IDE validation notes.
- Demo recording or screenshot filenames.
- Known limitations.
- Customer-safe support notes.
- Go/no-go decision.

## RC Decision

Use one of these decisions:

- `go`: all release-candidate gates passed and no blocking issues remain.
- `go-with-limitations`: the narrow launch path works, but documented limitations must be shown before private beta.
- `no-go`: a blocking issue prevents private beta or paid install.

Do not mark `go` unless at least one Android phone, the packaged Windows executable, and one launch IDE have completed the Phase 22 evidence path.
