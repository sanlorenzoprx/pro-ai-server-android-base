param(
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
& $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --name pro-ai-server `
    --distpath dist `
    --workpath build/pyinstaller `
    --specpath build/pyinstaller `
    --collect-data pro_ai_server `
    --add-data "embedded-tools/windows/platform-tools;embedded-tools/windows/platform-tools" `
    --exclude-module pytest `
    --exclude-module ruff `
    -m pro_ai_server.cli

$Exe = "dist\pro-ai-server\pro-ai-server.exe"
& $Exe validate-platform-tools --root .
& $Exe doctor
& $Exe setup --production
& $Exe status
& $Exe diagnose --output diagnostics.txt
