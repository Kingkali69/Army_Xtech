@echo off
REM Complete OMNI Launcher for Windows
REM Starts Infrastructure Operations Console + Engine + AI Chat
REM Requires Administrator privileges for M.I.T.E.L. device enforcement

REM Check for admin privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ======================================================================
    echo   ADMIN PRIVILEGES REQUIRED
    echo ======================================================================
    echo.
    echo M.I.T.E.L. device quarantine enforcement requires administrator rights.
    echo Please right-click this file and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

cd /d "%~dp0"

echo ======================================================================
echo   OMNI COMPLETE LAUNCHER - Windows [ADMIN MODE]
echo ======================================================================
echo.
echo Starting OMNI Infrastructure Operations Console...
echo Starting OMNI Engine...
echo Starting NEXUS AI Chat...
echo.

REM Kill any existing instances
echo Stopping any running OMNI processes...
taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 /nobreak >nul

REM Add firewall rules first (silent, may need admin but won't fail)
netsh advfirewall firewall add rule name="OMNI Port 8888" dir=in action=allow protocol=TCP localport=8888 >nul 2>&1
netsh advfirewall firewall add rule name="OMNI Port 8889" dir=in action=allow protocol=TCP localport=8889 >nul 2>&1

REM Start OMNI Engine
echo Starting OMNI Engine...
start /MIN "OMNI Core" C:\Users\kali\AppData\Local\Programs\Python\Python312\python.exe omni_core.py

REM Wait for core to fully initialize and connect to mesh
echo Waiting for OMNI Core to initialize and connect to mesh...
timeout /t 8 /nobreak >nul

REM Verify core is running before continuing
echo Verifying OMNI Core is running...
tasklist /FI "IMAGENAME eq python.exe" | find "python.exe" >nul
if errorlevel 1 (
    echo ERROR: OMNI Core failed to start
    pause
    exit /b 1
)

REM Start Web Console on port 8888
echo Starting OMNI Web Console...
timeout /t 2 /nobreak >nul
start /MIN "OMNI Console" C:\Users\kali\AppData\Local\Programs\Python\Python312\python.exe omni_web_console.py --port 8888

REM NEXUS AI Chat runs on Linux mesh node (192.168.1.161:8889)
REM No local AI chat needed - unified console has iframe to Linux NEXUS

REM Wait for servers to start
echo.
echo Waiting for servers to start...
timeout /t 5 /nobreak >nul

REM Wait longer for servers to actually start
timeout /t 8 /nobreak >nul

REM Open browser - ALWAYS use 127.0.0.1 (bypasses proxy and firewall issues)
echo.
echo Opening unified console...
echo.

REM Open unified console (has all 3 tabs: OMNI, M.I.T.E.L., NEXUS)
start http://127.0.0.1:8888

echo.
echo ======================================================================
echo   OMNI LAUNCHED
echo ======================================================================
echo.
echo OMNI Unified Console:
echo   http://127.0.0.1:8888
echo   (or http://localhost:8888 if proxy is disabled)
echo.
echo Tabs available:
echo   - OMNI Infrastructure (mesh topology, fabric health)
echo   - M.I.T.E.L. Security (device quarantine, zero-trust)
echo   - NEXUS AI (Linux-hosted at 192.168.1.161:8889)
echo.
echo Processes running in background.
echo.
echo To stop everything:
echo   Close this window or run: stop_omni_windows.bat
echo.
echo ======================================================================
echo.
echo Everything is running!
echo Browsers should open automatically...
echo If not, open the URLs above manually.
echo.
echo Press any key to close this window (servers will keep running)...
pause >nul
