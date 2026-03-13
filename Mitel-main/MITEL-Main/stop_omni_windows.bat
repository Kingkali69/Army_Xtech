@echo off
REM Stop all OMNI processes on Windows

echo Stopping OMNI...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *omni_web_console*" 2>nul
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *omni_ai_chat*" 2>nul
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *omni_core*" 2>nul
echo OMNI stopped
pause
