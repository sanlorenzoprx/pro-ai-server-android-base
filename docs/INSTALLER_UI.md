# Pro AI Server Installer UI

The first installer UI is a Windows-first text wrapper over the production installer state machine.

It is intentionally thin: it does not create a separate setup path. The UI screens are derived from `plan_production_installer`, the same production state machine used by `setup --production`.

## Preview

Run the UI preview without mutating a phone:

```powershell
pro-ai-server installer-ui
```

The preview shows:

- welcome and USB debugging checklist
- device detection
- hardware scan and model recommendation
- install progress
- test prompt result
- IDE configuration prompt
- success receipt

Advanced LAN and Tailscale modes are not shown in the first-run UI. The production UI is USB-first.

## Mock Recoverable Errors

Use a mocked failure to verify the error screen without a phone:

```powershell
pro-ai-server installer-ui --mock-failure termux-readiness
```

The error screen preserves:

- current failed step
- customer-facing recovery action
- debug detail for support

## Troubleshooting

If the preview fails, run:

```powershell
pro-ai-server setup --production
pro-ai-server validate-release
```

The UI should only depend on the production installer state machine. If UI output disagrees with `setup --production`, fix the shared state machine first.

