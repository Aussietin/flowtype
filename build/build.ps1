# Chains the full installer build. Run from the repo root:
#   .\build\build.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

$py = Join-Path $root "venv\Scripts\python.exe"

Write-Host "==> fetching model" -ForegroundColor Cyan
& $py build\fetch_model.py

Write-Host "==> freezing with PyInstaller" -ForegroundColor Cyan
& $py -m PyInstaller flowtype.spec --noconfirm --distpath build\dist --workpath build\work

Write-Host "==> building installer" -ForegroundColor Cyan
$iscc = (Get-Command iscc -ErrorAction SilentlyContinue).Source
foreach ($cand in @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe")) {
  if (-not $iscc -and (Test-Path $cand)) { $iscc = $cand }
}
if (-not $iscc -or -not (Test-Path $iscc)) { throw "iscc not found — winget install JRSoftware.InnoSetup" }
& $iscc installer.iss

Write-Host "==> done: installer-output\flowtype-setup.exe" -ForegroundColor Green
