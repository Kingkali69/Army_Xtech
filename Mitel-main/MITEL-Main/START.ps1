# OMNI Launcher for Windows PowerShell
# Just right-click -> Run with PowerShell

Set-Location $PSScriptRoot

Write-Host "OMNI Infrastructure Operations Console" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Starting web console..." -ForegroundColor Green
Write-Host ""

# Launch web console (auto-opens browser)
python omni_web_console.py $args
