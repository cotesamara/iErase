$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonPath = Join-Path $projectRoot ".venv\Scripts\python.exe"
$modelPath = Join-Path $env:USERPROFILE ".rembg\models\u2net\u2net.onnx"

if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw "The .venv Python was not found. Create the virtual environment first."
}

if (-not (Test-Path -LiteralPath $modelPath)) {
    throw "The offline u2net model was not found. Run AI mode once before building."
}

Push-Location $projectRoot
try {
    & $pythonPath -m PyInstaller --noconfirm --clean --distpath "release" "iErase.spec"
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed with exit code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "Build finished!"
Write-Host "Open: $projectRoot\release\iErase\iErase.exe"
