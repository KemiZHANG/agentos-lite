$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$FrontendDir = Join-Path $RepoRoot "frontend"

Write-Host "AgentOS Lite frontend startup" -ForegroundColor Cyan
Set-Location $FrontendDir

if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
    Write-Host "Installing frontend dependencies..."
    npm install
}

$env:NEXT_PUBLIC_API_BASE_URL = "http://127.0.0.1:8010"

Write-Host ""
Write-Host "Frontend dev server is starting." -ForegroundColor Green
Write-Host "Default URL: http://localhost:3000"
Write-Host "If port 3000 is busy, Next.js may switch to 3001. Use the URL printed by this terminal." -ForegroundColor Yellow
Write-Host "Backend API target: $env:NEXT_PUBLIC_API_BASE_URL"
Write-Host ""

npm run dev
