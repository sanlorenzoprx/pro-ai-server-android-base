# Android Compatibility

Pro AI Server should cast a wide net, but not a sloppy one. The production promise is strongest when the phone is Android 7.0 or newer, arm64, and has enough RAM for the selected local model.

## Compatibility Tiers

| Tier | Android | ABI | RAM | Model Tier | Production Position |
|---|---:|---|---:|---|---|
| Green | 10-15+ | arm64-v8a | 6 GB+ | professional | DevStack coding assistant with 1.5B/3B models |
| Yellow | 7-9 | arm64-v8a | 4-6 GB | lightweight | Lightweight local assistant; validate latency |
| Red | below 7 | any | any | unsupported | Not production supported |
| Red | any | 32-bit only | any | unsupported | Not recommended for local LLM production |
| Red | any | any | below 4 GB | unsupported | Below model floor for the supported product promise |

Run the compatibility gate:

```powershell
pro-ai-server android-compatibility --serial <device-serial>
```

The command reports Android compatibility tier, supported status, model tier, Termux installer source, Termux:API installer source, warnings, and blockers.

## Trust Lane Rules

- F-Droid, Termux, and Termux:API should come from the same trusted lane.
- Do not mix Play Store Termux with F-Droid Termux.
- If Play Store Termux is detected, stop and remove it before production install.
- If Termux and Termux:API were installed from different sources, warn and reinstall from one lane.
- Local APK installs require `--yes`.
- Downloaded APKs require URL plus SHA-256 and are deleted on checksum mismatch.

## APK Manifest Template

Use this schema when pinning exact APK releases:

```json
{
  "entries": [
    {
      "package_name": "org.fdroid.fdroid",
      "label": "F-Droid",
      "version": "TBD",
      "min_android": 7,
      "max_android": null,
      "url": "TBD",
      "sha256": "TBD",
      "source": "fdroid",
      "notes": "Pinned after release review."
    },
    {
      "package_name": "com.termux",
      "label": "Termux",
      "version": "TBD",
      "min_android": 7,
      "max_android": null,
      "url": "TBD",
      "sha256": "TBD",
      "source": "fdroid",
      "notes": "Current Termux production lane starts at Android 7.0."
    },
    {
      "package_name": "com.termux.api",
      "label": "Termux:API",
      "version": "TBD",
      "min_android": 7,
      "max_android": null,
      "url": "TBD",
      "sha256": "TBD",
      "source": "fdroid",
      "notes": "Must match the Termux trust lane."
    }
  ]
}
```

Do not replace `TBD` with live values until the exact releases and checksums have been reviewed.

## Model Guidance

- Green devices: professional profile first, with `qwen2.5-coder:3b` chat and `qwen2.5-coder:1.5b-base` autocomplete.
- Yellow devices: lightweight profile first, with smaller local models and explicit latency caveats.
- Red devices: do not sell as supported production installs.

## Hardware Evidence

Record real devices in `docs/PRODUCTION_RC.md` with phone model, Android version, ABI, RAM, storage, compatibility tier, selected model tier, Termux trust lane, and completed, blocked, or skipped smoke status.
