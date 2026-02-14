$ErrorActionPreference = "Stop"

if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    python -m pip install pyinstaller
}

Write-Host "Building launcher EXE..."
powershell -Command ".\tools\build_docker_launcher_exe.ps1"

$projectRoot = (Resolve-Path ".").Path
$packageDir = Join-Path $env:TEMP "ABoroOfficePackage"
if (Test-Path $packageDir) {
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $packageDir
}
New-Item -ItemType Directory -Path $packageDir -Force | Out-Null

$excludeDirs = @(
    (Join-Path $projectRoot ".git"),
    (Join-Path $projectRoot ".idea"),
    (Join-Path $projectRoot ".venv"),
    (Join-Path $projectRoot "dist"),
    (Join-Path $projectRoot "build"),
    (Join-Path $projectRoot "tests"),
    (Join-Path $projectRoot "docs"),
    (Join-Path $projectRoot "__pycache__"),
    (Join-Path $projectRoot ".pytest_cache"),
    (Join-Path $projectRoot ".mypy_cache"),
    (Join-Path $projectRoot "logs"),
    (Join-Path $projectRoot "tools\\installer\\staging"),
    (Join-Path $projectRoot "tools\\installer\\package"),
    (Join-Path $projectRoot "tools\\installer\\Output")
)

Write-Host "Preparing package directory..."
robocopy $projectRoot $packageDir /E /MT:16 /R:1 /W:1 /NFL /NDL `
    /XD $excludeDirs /XF "db.sqlite3" "*.spec" ".coverage" "WORKLOG_*.md" "PHASE*.md" | Out-Null

New-Item -ItemType Directory -Path (Join-Path $packageDir "bin") | Out-Null
$srcExe = Join-Path $projectRoot "dist\\ABoroOfficeDockerLauncher.exe"
$dstExe = Join-Path $packageDir "bin\\ABoroOfficeDockerLauncher.exe"
Copy-Item -Path $srcExe -Destination $dstExe -Force

New-Item -ItemType Directory -Path (Join-Path $packageDir "logs") | Out-Null

$iscc = Get-Command ISCC.exe -ErrorAction SilentlyContinue
if (-not $iscc) {
    $defaultPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    if (Test-Path $defaultPath) {
        $iscc = $defaultPath
    } else {
        throw "ISCC.exe not found. Please install Inno Setup 6."
    }
}

Write-Host "Building installer..."
$env:ABORO_PKG_DIR = $packageDir
& $iscc ".\tools\installer\ABoroOffice.iss"

Write-Host "Installer complete. Check .\tools\installer\Output\ABoroOfficeSetup.exe"
