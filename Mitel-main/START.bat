@echo off
REM OMNI Launcher for Windows
REM Just double-click or right-click -> Execute

cd /d "%~dp0"

echo OMNI Infrastructure Operations Console
echo =======================================
echo.
echo Starting web console...
echo.

REM Launch web console (auto-opens browser)
python omni_web_console.py %*

pause
