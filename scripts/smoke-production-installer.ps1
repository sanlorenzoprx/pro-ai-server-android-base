param(
    [switch]$WithPhone,
    [string]$Serial = "",
    [string]$Python = ".\.venv\Scripts\python.exe"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $Python)) {
    $Python = "python"
}

& $Python -m pip install -e ".[dev]"
& $Python -m ruff check .
& $Python -m pytest
& $Python -m pro_ai_server.cli validate-release
& $Python -m pro_ai_server.cli validate-platform-tools
& $Python -m pro_ai_server.cli setup --production
& $Python -m pro_ai_server.cli installer-ui
& $Python -m pro_ai_server.cli installer-ui --mock-failure termux-readiness
& $Python -m pro_ai_server.cli diagnose --output diagnostics.txt

if ($WithPhone) {
    $SerialArgs = @()
    if ($Serial.Trim()) {
        $SerialArgs = @("--serial", $Serial)
    }

    & $Python -m pro_ai_server.cli doctor
    & $Python -m pro_ai_server.cli scan @SerialArgs
    & $Python -m pro_ai_server.cli termux-check @SerialArgs
    & $Python -m pro_ai_server.cli generate-scripts --mode usb
    & $Python -m pro_ai_server.cli push-scripts @SerialArgs
    & $Python -m pro_ai_server.cli tunnel @SerialArgs
    & $Python -m pro_ai_server.cli configure-continue --mode usb
    & $Python -m pro_ai_server.cli server-check
    & $Python -m pro_ai_server.cli test-prompt
    & $Python -m pro_ai_server.cli status
}
