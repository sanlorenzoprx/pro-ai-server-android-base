# DevStack Demo Script

Use this script for the first Pro Agentic Coding Server demos with VS Code or Cursor. Keep the launch path USB-first until the local install, model response, and Continue config are stable.

## Setup

- Windows laptop with Pro AI Server installed.
- Android phone connected by USB with USB debugging authorized.
- Termux, Linux userland, Ollama, and the local model installed by the production installer.
- VS Code or Cursor installed with the Continue extension.
- Continue config written with the DevStack preset:

```powershell
pro-ai-server devstack-ide-status
pro-ai-server configure-devstack
```

For low-RAM demo phones, use the lightweight preset:

```powershell
pro-ai-server configure-devstack --profile lightweight
```

## Pre-Demo Smoke Checklist

Run this before every recording or live call:

- Phone is plugged in by USB and visible to Windows.
- USB debugging prompt is accepted on the phone.
- Production setup shows the ready state:

```powershell
pro-ai-server setup --production
```

- USB tunnel is active:

```powershell
pro-ai-server tunnel
```

- Server status is ready:

```powershell
pro-ai-server status
```

- Test prompt returns a valid response:

```powershell
pro-ai-server test-prompt
```

- Launch IDE readiness is green for either VS Code or Cursor:

```powershell
pro-ai-server devstack-ide-status
```

- Continue config uses the USB endpoint:

```powershell
pro-ai-server configure-devstack
```

Expected API base:

```text
http://localhost:11434
```

## Live Demo Run

1. Show the phone connected by USB.

   Say: "This is an Android phone running the local AI server. The laptop is using USB, not a cloud model endpoint."

2. Show Pro AI Server status.

```powershell
pro-ai-server status
```

   Say: "The installer detected the phone, selected a model for the hardware profile, and exposed the local endpoint through USB."

3. Show the Continue config preset.

```powershell
pro-ai-server configure-devstack
```

   Say: "This writes the Continue.dev config for VS Code or Cursor and backs up any existing config before changing it."

4. Open Cursor or VS Code.

   Use the IDE that `devstack-ide-status` shows as ready. Open a small local project with a simple function or test file.

5. Ask Continue chat a coding question.

   Prompt:

```text
Explain this function and suggest one small improvement.
```

   Say: "The response is coming from the phone through the local Ollama-compatible endpoint."

6. Show code assistance.

   Add a comment above a small function:

```text
// Add input validation and a basic error message
```

   Trigger Continue autocomplete or ask chat to produce the change, then apply a small edit. This is the coding assistance moment of the demo.

7. Close with the positioning line.

   Say: "For supported local workflows, this gives you a private AI coding assistant with no monthly AI model bill. Performance depends on the phone hardware and the selected local model."

## Fallback Lines

Use these when the phone is low-RAM or the model is slow:

- "This phone is on the lightweight profile, so the demo favors privacy and zero recurring model cost over cloud-model speed."
- "The installer selected a smaller model because this hardware has limited memory."
- "First-token latency can be slower on older phones; the important part is that the coding assistant is running locally over USB."
- "For larger code tasks, the Pro install tier should use a higher-RAM phone or a larger supported model."

If Continue is not ready:

- Run `pro-ai-server devstack-ide-status`.
- Install Continue with `pro-ai-server install-continue-extension --ide code` or `pro-ai-server install-continue-extension --ide cursor`.
- Re-run `pro-ai-server configure-devstack`.

If the model does not respond:

- Run `pro-ai-server test-prompt`.
- Run `pro-ai-server tunnel`.
- Run `pro-ai-server status`.
- Fall back to showing the terminal test prompt before returning to the IDE.

## Close

End with a simple call to action:

"If you have an old Android phone, we can turn it into a private local coding assistant for Cursor or VS Code. The starter path gets you running, and the pro install path handles setup, model choice, and IDE configuration."
