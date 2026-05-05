from __future__ import annotations

from dataclasses import dataclass

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
