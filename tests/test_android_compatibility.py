from pro_ai_server.android_compatibility import (
    ApkManifest,
    ApkManifestEntry,
    assess_android_compatibility,
    load_apk_manifest,
    manifest_install_options,
    parse_android_major,
    render_android_validation_lanes,
    render_apk_manifest,
)
from pro_ai_server.hardware import assess_device_profile


def make_profile(*, android_version: str, abi: str = "arm64-v8a", ram_gb: float = 6):
    return assess_device_profile(
        serial="ABC123",
        manufacturer="Acme",
        model="Test Phone",
        android_version=android_version,
        abi=abi,
        ram_gb=ram_gb,
        free_storage_gb=64,
    )


def test_parse_android_major_accepts_plain_and_dotted_versions():
    assert parse_android_major("13") == 13
    assert parse_android_major("8.1.0") == 8
    assert parse_android_major("preview") is None


def test_android_compatibility_green_for_modern_arm64_six_gb_phone():
    result = assess_android_compatibility(make_profile(android_version="13", ram_gb=6))

    assert result.tier == "green"
    assert result.supported is True
    assert result.model_tier == "professional"
    assert result.blockers == ()


def test_android_compatibility_yellow_for_android_12_plus_with_lower_ram():
    result = assess_android_compatibility(make_profile(android_version="12", ram_gb=4.5))

    assert result.tier == "yellow"
    assert result.supported is True
    assert result.model_tier == "lightweight"


def test_android_compatibility_red_for_android_below_12():
    result = assess_android_compatibility(make_profile(android_version="11", ram_gb=8))

    assert result.tier == "red"
    assert result.supported is False
    assert any("Android 12 or newer" in blocker for blocker in result.blockers)


def test_android_compatibility_red_for_32_bit_abi():
    result = assess_android_compatibility(make_profile(android_version="13", abi="armeabi-v7a", ram_gb=6))

    assert result.tier == "red"
    assert any("arm64 Android is required" in blocker for blocker in result.blockers)


def test_android_compatibility_blocks_play_store_termux_conflict():
    result = assess_android_compatibility(
        make_profile(android_version="13", ram_gb=6),
        termux_installer="com.android.vending",
    )

    assert result.tier == "red"
    assert any("Play Store Termux" in blocker for blocker in result.blockers)


def test_android_compatibility_warns_for_mixed_termux_sources():
    result = assess_android_compatibility(
        make_profile(android_version="13", ram_gb=6),
        termux_installer="org.fdroid.fdroid",
        termux_api_installer="com.google.android.packageinstaller",
    )

    assert result.tier == "green"
    assert any("different sources" in warning for warning in result.warnings)


def test_apk_manifest_selects_entry_by_android_range():
    manifest = ApkManifest(
        entries=(
            ApkManifestEntry(
                package_name="com.termux",
                label="Termux Android 7+",
                version="0.118.3",
                min_android=7,
                max_android=None,
                url="https://example.com/termux.apk",
                sha256="a" * 64,
                source="fdroid",
            ),
        )
    )

    assert manifest.for_package("com.termux", 13) is not None
    assert manifest.for_package("com.termux", 6) is None


def test_default_apk_manifest_is_complete_for_supported_android_12_lane():
    manifest = load_apk_manifest()

    for package_name in ("org.fdroid.fdroid", "com.termux", "com.termux.api"):
        entry = manifest.for_package(package_name, 13)
        assert entry is not None
        assert entry.version != "TBD"
        assert entry.url.startswith("https://f-droid.org/repo/")
        assert len(entry.sha256) == 64
        assert entry.sha256 != "TBD"

    options = manifest_install_options(manifest, 13)
    assert "--fdroid-url" in options
    assert "--termux-url" in options
    assert "--termux-api-url" in options
    assert manifest_install_options(manifest, 6) == ()


def test_render_apk_manifest_and_validation_lanes_include_android_bands():
    manifest_lines = render_apk_manifest(load_apk_manifest(), 14)
    lane_lines = render_android_validation_lanes()

    assert any("Android major: 14" in line for line in manifest_lines)
    assert any("Termux" in line for line in manifest_lines)
    assert any("android-12-13" in line for line in lane_lines)
    assert any("android-14-15-plus" in line for line in lane_lines)
