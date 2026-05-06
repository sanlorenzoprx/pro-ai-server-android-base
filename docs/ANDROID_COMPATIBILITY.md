# Android Compatibility

Pro AI Server should cast a wide net, but not a sloppy one. The current production promise starts at Android 12, requires arm64, and needs enough RAM for the selected local model.

## Compatibility Tiers

| Tier | Android | ABI | RAM | Model Tier | Production Position |
|---|---:|---|---:|---|---|
| Green | 12-15+ | arm64-v8a | 6 GB+ | professional | DevStack coding assistant with 1.5B/3B models |
| Yellow | 12-15+ | arm64-v8a | 4-6 GB | lightweight | Supported with lightweight models and latency caveats |
| Red | below 12 | any | any | unsupported | Not production supported |
| Red | any | 32-bit only | any | unsupported | Not recommended for local LLM production |
| Red | any | any | below 4 GB | unsupported | Below model floor for the supported product promise |

Run the compatibility gate:

```powershell
pro-ai-server android-compatibility --serial <device-serial>
```

The command reports Android compatibility tier, supported status, model tier, Termux installer source, Termux:API installer source, warnings, and blockers.

`setup --production` uses this compatibility model tier by default when no explicit `--profile` or `--ram-gb` override is provided. A yellow device therefore uses the lightweight production profile even when the raw hardware scan can recommend a more aggressive RAM-based profile.

Android 11 and below are outside the supported product promise even if the APK lane or Termux technically installs there.

Show the validation matrix:

```powershell
pro-ai-server android-validation-matrix
```

Show the pinned APK manifest and setup flags for a specific Android version:

```powershell
pro-ai-server apk-manifest --android-version 13
```

## Trust Lane Rules

- F-Droid, Termux, and Termux:API should come from the same trusted lane.
- Do not mix Play Store Termux with F-Droid Termux.
- If Play Store Termux is detected, stop and remove it before production install.
- If Termux and Termux:API were installed from different sources, warn and reinstall from one lane.
- Local APK installs require `--yes`.
- Downloaded APKs require URL plus SHA-256 and are deleted on checksum mismatch.

## Pinned APK Manifest

The production APK lane is pinned in `src/pro_ai_server/android-apk-manifest.json`. These values are not "latest"; they are reviewed stable artifacts for the F-Droid trust lane. Their technical minimum Android version is broader than the supported product promise, which now starts at Android 12.
The APK manifest template fields are `package_name`, `label`, `version`, `version_code`, `min_android`, `max_android`, `url`, `sha256`, `source`, and `notes`.

```json
{
  "entries": [
    {
      "package_name": "org.fdroid.fdroid",
      "label": "F-Droid Client",
      "version": "1.23.1",
      "version_code": 1023051,
      "min_android": 7,
      "max_android": null,
      "url": "https://f-droid.org/repo/org.fdroid.fdroid_1023051.apk",
      "sha256": "1dfce4269081693f10350dbabd26991a59d7c2bb81f870de54e5b113f4785b7a",
      "source": "fdroid",
      "notes": "Pinned to a stable F-Droid client with a published verification report."
    },
    {
      "package_name": "com.termux",
      "label": "Termux",
      "version": "0.118.3",
      "version_code": 1002,
      "min_android": 7,
      "max_android": null,
      "url": "https://f-droid.org/repo/com.termux_1002.apk",
      "sha256": "e6265a57eb5ca363808488e3b01955958bed93bc0c8a0d281849b363b11027ec",
      "source": "fdroid",
      "notes": "Stable suggested Termux release with broader technical compatibility than the supported product promise."
    },
    {
      "package_name": "com.termux.api",
      "label": "Termux:API",
      "version": "0.53.0",
      "version_code": 1002,
      "min_android": 7,
      "max_android": null,
      "url": "https://f-droid.org/repo/com.termux.api_1002.apk",
      "sha256": "4497dbbf81906df52e59ed387a5223d225aa0de3aca817cc557a621e4dadda44",
      "source": "fdroid",
      "notes": "Must match the Termux trust lane."
    }
  ]
}
```

Use the manifest directly during production execute:

```powershell
pro-ai-server setup --production --execute --yes --serial <device-serial> --use-pinned-apk-manifest
```

Manifest provenance:

- Termux F-Droid page lists current Termux releases and states the stable suggested `0.118.3` build requires Android 7.0 or newer.
- F-Droid package API reported `com.termux` suggested version code `1002` and `com.termux.api` suggested version code `1002` during review.
- F-Droid verification reports recorded the signed APK SHA-256 values pinned above.
- F-Droid API reported F-Droid client `1.23.2` as suggested during review, but this manifest pins `1.23.1` until the newer client has reviewed checksum evidence in our manifest.

## Android Validation Lanes

| Lane | Android | ABI | RAM | Model Tier | Status | Product Promise |
|---|---:|---|---:|---|---|---|
| android-12-13-yellow | 12-13 | arm64-v8a | 4-6 GB | lightweight | partially-live-validated | Supported production lane with lightweight models |
| android-12-13-green | 12-13 | arm64-v8a | 6 GB+ | professional | device-needed | Supported production lane with professional models |
| android-14-15-plus-yellow | 14-15+ | arm64-v8a | 4-6 GB | lightweight | device-needed | Supported production lane with newer Android install behavior still under validation |
| android-14-15-plus-green | 14-15+ | arm64-v8a | 6 GB+ | professional | device-needed | Supported production lane with newer Android install behavior still under validation |

The Moto g 5G (2022) live device is Android 13 and belongs to the `android-12-13-yellow` lane because its 5.54 GB RAM keeps it in the lightweight model tier.

## Model Guidance

- Green devices: professional profile first, with `qwen2.5-coder:3b` chat and `qwen2.5-coder:1.5b-base` autocomplete.
- Yellow devices: lightweight profile first, with smaller local models and explicit latency caveats.
- Red devices: do not sell as supported production installs.

## Hardware Evidence

Record real devices in `docs/PRODUCTION_RC.md` with phone model, Android version, ABI, RAM, storage, compatibility tier, selected model tier, Termux trust lane, and completed, blocked, or skipped smoke status.
