# Troubleshooting

Use these checks when the Windows host, Android phone, Termux, Ollama, or Continue does not behave like the MVP workflow expects.

## ADB and Device Selection

### No device found

Run:

```powershell
pro-ai-server doctor
adb devices
```

Confirm the phone is connected by USB, USB debugging is enabled in Android developer options, and the cable supports data. Reconnect the phone, then rerun the command that failed.

Release builds should use bundled ADB from `embedded-tools/windows/platform-tools/adb.exe`. If bundled ADB is missing or invalid, run `pro-ai-server validate-platform-tools`. As a fallback for development machines, install Android Studio or the Android SDK Platform Tools and make sure `adb.exe` is on `PATH`.

The MVP has no fastboot flow: fastboot is not used, and `fastboot.exe` is not required.

### Unauthorized device

If `adb devices` shows `unauthorized`, unlock the phone and accept the USB debugging prompt. If the prompt does not appear, revoke USB debugging authorizations in Android developer options, reconnect USB, and accept the new prompt.

### Multiple devices require --serial

When more than one Android device or emulator is visible, use the serial from `adb devices`:

```powershell
pro-ai-server scan --serial <device-serial>
pro-ai-server termux-check --serial <device-serial>
pro-ai-server push-scripts --serial <device-serial>
pro-ai-server tunnel --serial <device-serial>
```

## Termux Readiness

Run this before pushing scripts:

```powershell
pro-ai-server termux-check
```

If Termux is missing, install Termux from F-Droid or GitHub, then open it once. If Termux:API is missing, install Termux:API, then rerun `termux-check`. If Termux home is not initialized, open Termux once on the phone so `/data/data/com.termux/files/home` exists.

Use the installer helper to open the trusted F-Droid package pages on the connected phone:

```powershell
pro-ai-server install-termux-apps --serial <device-serial>
```

If Android blocks F-Droid as an unpublished or unknown app source, allow F-Droid from the "Install unknown apps" screen opened by the helper command.

If F-Droid is not installed, provide a locally reviewed F-Droid APK:

```powershell
pro-ai-server install-termux-apps --serial <device-serial> --fdroid-apk C:\path\to\fdroid.apk --yes
```

For pinned APK downloads, provide both URL and SHA-256:

```powershell
pro-ai-server install-termux-apps --serial <device-serial> --fdroid-url https://example.com/fdroid.apk --fdroid-sha256 <sha256> --yes
```

For a fully scripted path with local APKs that you already reviewed:

```powershell
pro-ai-server install-termux-apps --serial <device-serial> --fdroid-apk C:\path\to\fdroid.apk --termux-apk C:\path\to\termux.apk --termux-api-apk C:\path\to\termux-api.apk --yes
```

The helper refuses APK downloads without a SHA-256 and removes files that fail checksum verification.

The production setup command can also drive this lane:

```powershell
pro-ai-server setup --production --execute --yes --serial <device-serial> --fdroid-apk C:\path\to\fdroid.apk --termux-apk C:\path\to\termux.apk --termux-api-apk C:\path\to\termux-api.apk
```

If setup pauses before script push, approve any Android install prompts, open Termux once, and rerun the same setup command. This is a recoverable Android stop, not a silent success.

To use the bundled reviewed APK manifest instead of supplying URL/SHA-256 flags manually:

```powershell
pro-ai-server setup --production --execute --yes --serial <device-serial> --use-pinned-apk-manifest
```

If this fails on Android 11 or below, the phone is outside the supported product promise. If it fails on Android 14/15+, record the install prompt or background restriction in `docs/PRODUCTION_RC.md` before changing the promise.

Termux:Widget manual placement is still required. Install Termux:Widget, confirm the generated `Start Pro AI Server` shortcut is in `~/.shortcuts`, then add the widget or shortcut from the Android home screen.

### Production installer stops at Termux readiness

Run:

```powershell
pro-ai-server installer-ui --mock-failure termux-readiness
pro-ai-server termux-check
```

Install Termux and Termux:API from the same trusted source. Open Termux once before rerunning setup so the Termux home directory exists.

### Android blocks the Termux phone stack runner

Production setup pushes `bootstrap-phone-stack.sh` and requests it through Termux's RUN_COMMAND service. If Android or Termux blocks that request, open Termux and run:

```sh
~/bootstrap-phone-stack.sh
```

The runner writes `~/pro-ai-server-bootstrap.log`, starts the server with `~/start-pro-ai-server.sh`, and writes server output to `~/pro-ai-server.log`.

## Ollama and Models

### Ollama not responding on localhost:11434

For USB mode, start the generated script inside Termux, then create the USB forward tunnel:

```powershell
pro-ai-server tunnel
```

Confirm Continue points to `http://localhost:11434`. In USB mode, Ollama should bind to `127.0.0.1:11434` on the phone and Windows reaches it through `adb forward tcp:11434 tcp:11434`.

For LAN or Tailscale mode, confirm the phone script was generated for that mode and that Continue uses the explicit `--host` value.

### Missing models

Run the generated model installer inside Termux:

```sh
~/install-models.sh
```

If Continue reports missing models, compare the model names in `%USERPROFILE%\.continue\config.yaml` with `ollama list` inside Termux. Re-run `pro-ai-server generate-scripts --mode usb` if you changed the profile or model plan.

### Test prompt failed

Run:

```powershell
pro-ai-server server-check
pro-ai-server test-prompt
pro-ai-server status
```

If `test-prompt` reports a missing model, run `~/install-models.sh` in Termux. If it reports connection refused, confirm `~/start-pro-ai-server.sh` is running and recreate the USB tunnel with `pro-ai-server tunnel`.

### USB tunnel failure

Run:

```powershell
adb forward --list
pro-ai-server tunnel
pro-ai-server status
```

If the tunnel is missing after reconnecting the phone, rerun `pro-ai-server tunnel --serial <device-serial>`. Keep the USB cable connected while using Continue in USB mode.

## Continue Configuration

`pro-ai-server configure-continue` writes `%USERPROFILE%\.continue\config.yaml`. When an existing Continue config is present, the Continue backup is written next to it with this filename pattern:

```text
config.yaml.pro-ai-server-backup-YYYYMMDD-HHMMSS
```

Keep that backup if you need to restore previous Continue settings.

## LAN and Tailscale Exposure

USB mode is the safest default because Continue uses `http://localhost:11434` through an ADB tunnel. LAN mode exposes Ollama on the local network, and LAN or Tailscale scripts bind Ollama to `0.0.0.0:11434`.

Use LAN only on trusted networks:

```powershell
pro-ai-server configure-continue --mode lan --host 192.168.1.50
```

For Tailscale, prefer the private Tailscale hostname or the `100.x.x.x` Tailscale IP:

```powershell
pro-ai-server configure-continue --mode tailscale --host pro-ai-phone
pro-ai-server configure-continue --mode tailscale --host 100.x.x.x
```

## Release Validation

Before publishing or handing off a build, run:

```powershell
pro-ai-server validate-release
```

`validate-release` checks bundled ADB runtime files, package data for embedded tools, and CI gates. Use `pro-ai-server validate-platform-tools` for a narrower bundled ADB validation when troubleshooting host ADB problems.

For production installer smoke checks, run:

```powershell
scripts/smoke-production-installer.ps1
```

Use `-WithPhone` only when a USB-connected, authorized Android phone is available.
