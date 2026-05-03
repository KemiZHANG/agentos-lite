$ErrorActionPreference = "Stop"

$BaseUrl = if ($env:AGENTOS_BACKEND_URL) { $env:AGENTOS_BACKEND_URL } else { "http://127.0.0.1:8010" }

Write-Host "Checking AgentOS Lite backend at $BaseUrl" -ForegroundColor Cyan

try {
    $Health = Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get
    Write-Host "Health: $($Health.status)" -ForegroundColor Green

    $Settings = Invoke-RestMethod -Uri "$BaseUrl/settings" -Method Get
    Write-Host ""
    Write-Host "Safe provider status:" -ForegroundColor Green
    Write-Host "mode:           $($Settings.current_mode)"
    Write-Host "provider:       $($Settings.llm_provider)"
    Write-Host "model:          $($Settings.active_model)"
    Write-Host "key_configured: $($Settings.llm_api_key_configured)"
    Write-Host "fallback:       $($Settings.llm_fallback_to_mock)"
    Write-Host "demo_mode:      $($Settings.demo_mode)"
    Write-Host "daily_limit:    $($Settings.max_calls_per_day)"
    Write-Host "remaining:      $($Settings.current_session_remaining_calls)"
    Write-Host "embedding:      $($Settings.embedding_provider)"
    Write-Host "rag_mode:       $($Settings.rag_mode)"
} catch {
    Write-Host "Backend check failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Make sure scripts/start_backend.ps1 is running in another terminal."
    exit 1
}
