from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

from pro_ai_server.hardware import DeviceProfile


PLAY_STORE_INSTALLER = "com.android.vending"
FDROID_INSTALLER = "org.fdroid.fdroid"
PACKAGE_INSTALLER = "com.google.android.packageinstaller"


@dataclass(frozen=True)
class AndroidCompatibilityResult:
    tier: str
    supported: bool
    model_tier: str
    summary: str
    warnings: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()


@dataclass(frozen=True)
class ApkManifestEntry:
    package_name: str
    label: str
    version: str
    min_android: int
    max_android: int | None
    url: str
    sha256: str
    source: str
    notes: str = ""
    version_code: int | None = None


@dataclass(frozen=True)
class ApkManifest:
    entries: tuple[ApkManifestEntry, ...]

    def for_package(self, package_name: str, android_major: int) -> ApkManifestEntry | None:
        for entry in self.entries:
            if entry.package_name != package_name:
                continue
            if android_major < entry.min_android:
                continue
            if entry.max_android is not None and android_major > entry.max_android:
                continue
            return entry
        return None

    def entries_for_android(self, android_major: int) -> tuple[ApkManifestEntry, ...]:
        return tuple(
            entry
            for entry in self.entries
            if android_major >= entry.min_android
            and (entry.max_android is None or android_major <= entry.max_android)
        )


@dataclass(frozen=True)
class AndroidValidationLane:
    key: str
    android_range: str
    min_android: int
    max_android: int | None
    abi: str
    ram_gb: str
    model_tier: str
    product_promise: str
    validation_status: str
    notes: str = ""


ANDROID_VALIDATION_LANES: tuple[AndroidValidationLane, ...] = (
    AndroidValidationLane(
        key="android-7-9-yellow",
        android_range="7-9",
        min_android=7,
        max_android=9,
        abi="arm64-v8a",
        ram_gb="4-6",
        model_tier="lightweight",
        product_promise="Lightweight local assistant with latency caveats.",
        validation_status="device-needed",
        notes="Use current Termux stable lane; no Android 5/6 archive promise.",
    ),
    AndroidValidationLane(
        key="android-10-13-green",
        android_range="10-13",
        min_android=10,
        max_android=13,
        abi="arm64-v8a",
        ram_gb="6+",
        model_tier="professional",
        product_promise="DevStack coding assistant with 1.5B/3B models.",
        validation_status="partially-live-validated",
        notes="Moto g 5G Android 13 is live yellow/lightweight because RAM is under 6 GB.",
    ),
    AndroidValidationLane(
        key="android-14-15-green",
        android_range="14-15",
        min_android=14,
        max_android=15,
        abi="arm64-v8a",
        ram_gb="6+",
        model_tier="professional",
        product_promise="DevStack coding assistant after stricter install behavior is validated.",
        validation_status="device-needed",
        notes="Validate unknown-app install prompts and background behavior on Android 14/15.",
    ),
)


def load_apk_manifest(path: Path | None = None) -> ApkManifest:
    if path is None:
        text = resources.files("pro_ai_server").joinpath("android-apk-manifest.json").read_text(encoding="utf-8")
    else:
        text = path.read_text(encoding="utf-8")
    payload = json.loads(text)
    entries = tuple(_manifest_entry_from_mapping(entry) for entry in payload.get("entries", ()))
    return ApkManifest(entries=entries)


def manifest_install_options(manifest: ApkManifest, android_major: int) -> tuple[str, ...]:
    options: list[str] = []
    for package_name, url_flag, sha_flag in (
        ("org.fdroid.fdroid", "--fdroid-url", "--fdroid-sha256"),
        ("com.termux", "--termux-url", "--termux-sha256"),
        ("com.termux.api", "--termux-api-url", "--termux-api-sha256"),
    ):
        entry = manifest.for_package(package_name, android_major)
        if entry is None:
            continue
        options.extend((url_flag, entry.url, sha_flag, entry.sha256))
    return tuple(options)


def render_apk_manifest(manifest: ApkManifest, android_major: int | None = None) -> tuple[str, ...]:
    entries = manifest.entries if android_major is None else manifest.entries_for_android(android_major)
    lines = ["Pinned APK manifest"]
    if android_major is not None:
        lines.append(f"Android major: {android_major}")
    for entry in entries:
        version = entry.version if entry.version_code is None else f"{entry.version} ({entry.version_code})"
        lines.extend(
            (
                f"- {entry.label}: {version}",
                f"  Package: {entry.package_name}",
                f"  Android: {entry.min_android}+"
                if entry.max_android is None
                else f"  Android: {entry.min_android}-{entry.max_android}",
                f"  URL: {entry.url}",
                f"  SHA-256: {entry.sha256}",
                f"  Source: {entry.source}",
            )
        )
        if entry.notes:
            lines.append(f"  Notes: {entry.notes}")
    if android_major is not None:
        options = manifest_install_options(manifest, android_major)
        if options:
            lines.append("Setup options:")
            lines.append(" ".join(options))
    return tuple(lines)


def render_android_validation_lanes() -> tuple[str, ...]:
    lines = ["Android validation lanes"]
    for lane in ANDROID_VALIDATION_LANES:
        lines.append(
            f"- {lane.key}: Android {lane.android_range}, {lane.abi}, {lane.ram_gb} GB RAM, "
            f"{lane.model_tier}, {lane.validation_status}"
        )
        lines.append(f"  Promise: {lane.product_promise}")
        if lane.notes:
            lines.append(f"  Notes: {lane.notes}")
    return tuple(lines)


def assess_android_compatibility(
    profile: DeviceProfile,
    *,
    termux_installer: str | None = None,
    termux_api_installer: str | None = None,
) -> AndroidCompatibilityResult:
    android_major = parse_android_major(profile.android_version)
    warnings: list[str] = []
    blockers: list[str] = []

    if android_major is None:
        blockers.append("Unable to parse Android major version.")
        android_major_value = 0
    else:
        android_major_value = android_major

    if android_major_value < 7:
        blockers.append("Android 7.0 or newer is required for the supported Termux production lane.")

    if profile.abi.lower() not in {"arm64-v8a", "aarch64"}:
        blockers.append("arm64 Android is required for the supported local LLM production lane.")

    if profile.ram_gb < 4:
        warnings.append("RAM under 4 GB is below the supported model floor; use a better phone.")

    _append_installer_conflicts(warnings, blockers, termux_installer, termux_api_installer)

    if blockers:
        tier = "red"
        supported = False
        model_tier = "unsupported"
        summary = "Not production supported."
    elif android_major_value >= 10 and profile.ram_gb >= 6:
        tier = "green"
        supported = True
        model_tier = "professional"
        summary = "Production candidate for DevStack with professional model profile."
    elif android_major_value >= 7 and profile.ram_gb >= 4:
        tier = "yellow"
        supported = True
        model_tier = "lightweight"
        summary = "Supported for lightweight local assistant workflows; validate latency."
    else:
        tier = "red"
        supported = False
        model_tier = "unsupported"
        summary = "Not production supported."

    return AndroidCompatibilityResult(
        tier=tier,
        supported=supported,
        model_tier=model_tier,
        summary=summary,
        warnings=tuple(warnings),
        blockers=tuple(blockers),
    )


def parse_android_major(version: str) -> int | None:
    head = version.strip().split(".", maxsplit=1)[0]
    try:
        return int(head)
    except ValueError:
        return None


def render_android_compatibility(result: AndroidCompatibilityResult) -> tuple[str, ...]:
    lines = [
        f"Compatibility tier: {result.tier}",
        f"Supported: {result.supported}",
        f"Model tier: {result.model_tier}",
        f"Summary: {result.summary}",
    ]
    lines.extend(f"Warning: {warning}" for warning in result.warnings)
    lines.extend(f"Blocker: {blocker}" for blocker in result.blockers)
    return tuple(lines)


def _manifest_entry_from_mapping(entry: dict[str, Any]) -> ApkManifestEntry:
    return ApkManifestEntry(
        package_name=str(entry["package_name"]),
        label=str(entry["label"]),
        version=str(entry["version"]),
        version_code=entry.get("version_code"),
        min_android=int(entry["min_android"]),
        max_android=None if entry.get("max_android") is None else int(entry["max_android"]),
        url=str(entry["url"]),
        sha256=str(entry["sha256"]),
        source=str(entry["source"]),
        notes=str(entry.get("notes", "")),
    )


def _append_installer_conflicts(
    warnings: list[str],
    blockers: list[str],
    termux_installer: str | None,
    termux_api_installer: str | None,
) -> None:
    installers = tuple(installer for installer in (termux_installer, termux_api_installer) if installer)
    if not installers:
        return
    if any(installer == PLAY_STORE_INSTALLER for installer in installers):
        blockers.append("Play Store Termux builds conflict with the supported F-Droid/GitHub production lane.")
    non_fdroid = tuple(
        installer
        for installer in installers
        if installer not in {FDROID_INSTALLER, PACKAGE_INSTALLER, PLAY_STORE_INSTALLER}
    )
    if non_fdroid:
        warnings.append("Termux installer source is not F-Droid; verify signatures before continuing.")
    if termux_installer and termux_api_installer and termux_installer != termux_api_installer:
        warnings.append("Termux and Termux:API were installed from different sources; reinstall from one trust lane.")
