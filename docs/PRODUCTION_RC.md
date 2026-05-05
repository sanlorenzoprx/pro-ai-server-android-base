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
| TBD | TBD | TBD | TBD | TBD | TBD | blocked | blocked | blocked | blocked | blocked | blocked | blocked | blocked | blocked |

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
| ADB detection | `pro-ai-server scan --serial <serial>` | Phone is detected and authorized | blocked | TBD |
| Production plan | `pro-ai-server setup --production` | USB-first production plan renders | blocked | TBD |
| Production execute | `pro-ai-server setup --execute --yes --serial <serial>` | Setup completes or records recoverable failure | blocked | TBD |
| Termux readiness | `pro-ai-server termux-check --serial <serial>` | Termux, Termux:API, and home state are ready | blocked | TBD |
| Script push | `pro-ai-server push-scripts --serial <serial>` | Termux scripts are delivered | blocked | TBD |
| USB tunnel | `pro-ai-server tunnel --serial <serial>` | `adb reverse tcp:11434 tcp:11434` is active | blocked | TBD |
| Server status | `pro-ai-server status --serial <serial>` | Local server readiness is visible | blocked | TBD |
| Model inventory | `pro-ai-server server-check --serial <serial>` | Required model inventory is visible | blocked | TBD |
| Test prompt | `pro-ai-server test-prompt --serial <serial>` | Local model returns a valid response | blocked | TBD |

Evidence log:

| Evidence | Filename Or Command Output Summary | Status | Notes |
|---|---|---|---|
| Phone photo | TBD | blocked | Show USB-connected Android phone |
| Terminal smoke output | TBD | blocked | Save command output or summary |
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
| TBD | TBD | TBD | TBD |

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
