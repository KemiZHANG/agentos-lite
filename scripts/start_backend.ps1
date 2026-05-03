$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$BackendDir = Join-Path $RepoRoot "backend"
$VenvDir = Join-Path $BackendDir ".venv"
$PythonExe = Join-Path $VenvDir "Scripts\python.exe"
$ActivateScript = Join-Path $VenvDir "Scripts\Activate.ps1"

Write-Host "AgentOS Lite backend startup" -ForegroundColor Cyan
Set-Location $BackendDir

if (-not (Test-Path $PythonExe)) {
    Write-Host "Creating backend virtual environment..."
    python -m venv .venv
}

Write-Host "Activating virtual environment..."
. $ActivateScript

Write-Host "Installing backend dependencies..."
python -m pip install -r requirements.txt

$env:PYTHONPATH = ".."
$Port = if ($env:AGENTOS_BACKEND_PORT) { $env:AGENTOS_BACKEND_PORT } else { "8010" }

Write-Host ""
Write-Host "Backend will run at http://127.0.0.1:$Port" -ForegroundColor Green
Write-Host "Health check: http://127.0.0.1:$Port/health"
Write-Host "Settings:     http://127.0.0.1:$Port/settings"
Write-Host "Keep this window open while using AgentOS Lite." -ForegroundColor Yellow
Write-Host ""

uvicorn app.main:app --reload --host 127.0.0.1 --port $Port
