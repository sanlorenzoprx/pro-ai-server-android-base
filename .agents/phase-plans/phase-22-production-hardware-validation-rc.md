# Phase 22: Production Hardware Validation and First Release Candidate

## Goal

Move Pro AI Server and Pro Agentic Coding Server from build-ready to release-candidate ready by validating the Windows executable, USB-first Android hardware flow, Continue IDE integration, and release evidence on real devices.

## Non-Goals

- Do not add LAN or Tailscale as a release blocker.
- Do not expand launch IDE support beyond VS Code and Cursor.
- Do not scale creator, affiliate, partner, or paid traffic before hardware smoke evidence exists.
- Do not promise performance beyond the measured phone profile.
- Do not ship the first release candidate without a documented go/no-go decision.

## Build Tickets

| Ticket | Title | Depends On |
|---|---|---|
| TKT-P22-001 | Production hardware smoke matrix | Phase 20 installer, Phase 21 DevStack docs |
| TKT-P22-001B | Automated F-Droid and Termux bootstrap install path | TKT-P22-001 |
| TKT-P22-001D | Android compatibility and APK manifest matrix | TKT-P22-001B |
| TKT-P22-001E | Use compatibility model tier in production setup | TKT-P22-001D |
| TKT-P22-002 | Packaged Windows exe release-candidate smoke | TKT-P22-001 |
| TKT-P22-003 | Live Continue IDE validation | TKT-P22-001, TKT-P22-002 |
| TKT-P22-004 | Release evidence bundle | TKT-P22-002, TKT-P22-003 |
| TKT-P22-005 | RC go/no-go closeout | TKT-P22-004 |

## Required Contracts

- `.agents/contracts/phase-22/hardware-smoke-contract.md`
- `.agents/contracts/phase-22/fdroid-termux-bootstrap-contract.md`
- `.agents/contracts/phase-22/android-compatibility-contract.md`
- `.agents/contracts/phase-22/windows-rc-contract.md`
- `.agents/contracts/phase-22/ide-live-validation-contract.md`
- `.agents/contracts/phase-22/release-evidence-contract.md`
- `.agents/contracts/phase-22/rc-go-no-go-contract.md`

## Validation

```bash
ruff check .
pytest
pro-ai-server validate-release
scripts/build-windows-exe.ps1
scripts/smoke-production-installer.ps1
scripts/smoke-production-installer.ps1 -WithPhone
dist/pro-ai-server/pro-ai-server.exe validate-release
dist/pro-ai-server/pro-ai-server.exe setup --production
dist/pro-ai-server/pro-ai-server.exe test-prompt
dist/pro-ai-server/pro-ai-server.exe devstack-ide-status
dist/pro-ai-server/pro-ai-server.exe configure-devstack
```

## Closeout Criteria

- At least one real Android phone has completed the USB-first hardware smoke.
- The packaged Windows executable has completed no-phone and with-phone smoke paths.
- VS Code or Cursor has answered a Continue chat request through the local phone endpoint.
- A coding assistance moment has been captured or manually recorded.
- Release evidence records device model, Android version, RAM profile, selected models, IDE, command results, failures, and recovery steps.
- The release candidate has a written go/no-go decision with known limitations.
