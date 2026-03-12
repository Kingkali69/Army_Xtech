# Complete OMNI Launcher for Windows (PowerShell)
# Starts Infrastructure Operations Console + Engine + AI Chat
# Right-click and "Run with PowerShell" or double-click if associated

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  OMNI COMPLETE LAUNCHER - Windows" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Starting OMNI Infrastructure Operations Console..."
Write-Host "Starting OMNI Engine..."
Write-Host "Starting NEXUS AI Chat..."
Write-Host ""

# Kill any existing instances
Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*omni_web_console*" -or
    $_.CommandLine -like "*omni_ai_chat*" -or
    $_.CommandLine -like "*omni_core*"
} | Stop-Process -Force -ErrorAction SilentlyContinue

Start-Sleep -Seconds 1

# Start Infrastructure Operations Console (port 8888)
Write-Host "Starting Infrastructure Operations Console..."
$consoleJob = Start-Job -ScriptBlock {
    Set-Location $using:scriptPath
    python omni_web_console.py --port 8888 --no-browser
}
Write-Host "  Console started (Job ID: $($consoleJob.Id))"

# Start AI Chat (port 8889)
Write-Host "Starting NEXUS AI Chat..."
$aiJob = Start-Job -ScriptBlock {
    Set-Location $using:scriptPath
    python omni_ai_chat.py --port 8889 --no-browser
}
Write-Host "  AI Chat started (Job ID: $($aiJob.Id))"

# Wait for servers to start
Write-Host ""
Write-Host "Waiting for servers to start..."
Start-Sleep -Seconds 5

# Get local IP
$localIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {
    $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*"
}).IPAddress | Select-Object -First 1

if (-not $localIP) {
    $localIP = "127.0.0.1"
}

# Open browsers
Write-Host ""
Write-Host "Opening browsers..."
Write-Host ""

# Open Operations Console (use 127.0.0.1 to bypass proxy)
Start-Process "http://127.0.0.1:8888"
Start-Sleep -Seconds 1

# Open AI Chat (use 127.0.0.1 to bypass proxy)
Start-Process "http://127.0.0.1:8889"

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "  OMNI LAUNCHED" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Infrastructure Operations Console:" -ForegroundColor Yellow
Write-Host "  http://127.0.0.1:8888" -ForegroundColor White
Write-Host "  (or http://localhost:8888 if proxy is disabled)" -ForegroundColor Gray
Write-Host ""
Write-Host "NEXUS AI Chat:" -ForegroundColor Yellow
Write-Host "  http://127.0.0.1:8889" -ForegroundColor White
Write-Host "  (or http://localhost:8889 if proxy is disabled)" -ForegroundColor Gray
Write-Host ""
Write-Host "Processes running in background jobs."
Write-Host ""
Write-Host "To stop everything:" -ForegroundColor Yellow
Write-Host "  Run: .\stop_omni_windows.ps1" -ForegroundColor White
Write-Host "  Or: Stop-Job -Id $($consoleJob.Id),$($aiJob.Id)" -ForegroundColor White
Write-Host ""
Write-Host "======================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Everything is running!" -ForegroundColor Green
Write-Host "Browsers should open automatically..."
Write-Host "If not, open the URLs above manually."
Write-Host ""
Write-Host "Press any key to close this window (servers will keep running)..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
