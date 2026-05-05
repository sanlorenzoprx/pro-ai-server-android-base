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

$EntryPoint = "build\pyinstaller\pro_ai_server_entry.py"
$PlatformTools = (Resolve-Path "embedded-tools\windows\platform-tools").Path
New-Item -ItemType Directory -Force -Path (Split-Path $EntryPoint) | Out-Null
@"
from pro_ai_server.cli import app

if __name__ == "__main__":
    app()
"@ | Set-Content -Path $EntryPoint -Encoding UTF8

& $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --name pro-ai-server `
    --distpath dist `
    --workpath build/pyinstaller `
    --specpath build/pyinstaller `
    --collect-data pro_ai_server `
    --add-data "$PlatformTools;embedded-tools/windows/platform-tools" `
    --exclude-module pytest `
    --exclude-module ruff `
    $EntryPoint

$Exe = "dist\pro-ai-server\pro-ai-server.exe"
& $Exe validate-platform-tools --root .
& $Exe doctor
& $Exe setup --production --profile lightweight
& $Exe status
& $Exe diagnose --output diagnostics.txt
