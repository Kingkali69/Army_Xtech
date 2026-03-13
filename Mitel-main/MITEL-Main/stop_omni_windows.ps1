# Stop all OMNI processes on Windows

Write-Host "Stopping OMNI..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*omni_web_console*" -or
    $_.CommandLine -like "*omni_ai_chat*" -or
    $_.CommandLine -like "*omni_core*"
} | Stop-Process -Force -ErrorAction SilentlyContinue

Get-Job | Where-Object {
    $_.Command -like "*omni*"
} | Stop-Job -ErrorAction SilentlyContinue

Write-Host "OMNI stopped" -ForegroundColor Green
