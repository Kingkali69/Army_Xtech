@echo off
REM GhostHUD Windows - One-Click Startup
REM Works from ANY directory, ANY folder name
REM Auto-detects master IP and creates desktop shortcut

REM Get absolute path of script location (works even if moved/renamed)
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Auto-detect master IP (try known IPs first, then scan subnet)
set "MASTER_IP=192.168.1.116"

REM Try known IPs first (faster)
for %%I in (192.168.1.116 192.168.1.235 192.168.1.14) do (
    powershell -Command "Test-NetConnection -ComputerName %%I -Port 7890 -InformationLevel Quiet -WarningAction SilentlyContinue" >nul 2>&1
    if errorlevel 0 (
        set "MASTER_IP=%%I"
        echo [*] Found master at %%I:7890
        goto :found
    )
)

REM If not found, try scanning subnet (slower)
echo [*] Scanning local network for master...
for /L %%I in (1,1,255) do (
    set "TEST_IP=192.168.1.%%I"
    powershell -Command "Test-NetConnection -ComputerName 192.168.1.%%I -Port 7890 -InformationLevel Quiet -WarningAction SilentlyContinue" >nul 2>&1
    if errorlevel 0 (
        set "MASTER_IP=192.168.1.%%I"
        echo [*] Found master at 192.168.1.%%I:7890
        goto :found
    )
)
:found

REM Create desktop shortcut if it doesn't exist
set "DESKTOP=%USERPROFILE%\Desktop"
if exist "%DESKTOP%" (
    if not exist "%DESKTOP%\GhostHUD.lnk" (
        REM Create VBScript to create shortcut
        echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\create_shortcut.vbs"
        echo sLinkFile = "%DESKTOP%\GhostHUD.lnk" >> "%TEMP%\create_shortcut.vbs"
        echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\create_shortcut.vbs"
        echo oLink.TargetPath = "%SCRIPT_DIR%START_GHOSTHUD.bat" >> "%TEMP%\create_shortcut.vbs"
        echo oLink.WorkingDirectory = "%SCRIPT_DIR%" >> "%TEMP%\create_shortcut.vbs"
        echo oLink.Description = "GhostHUD Cybersecurity Platform" >> "%TEMP%\create_shortcut.vbs"
        echo oLink.Save >> "%TEMP%\create_shortcut.vbs"
        cscript //nologo "%TEMP%\create_shortcut.vbs" >nul 2>&1
        del "%TEMP%\create_shortcut.vbs" >nul 2>&1
        echo [+] Desktop shortcut created!
    )
)

REM Main execution
cls
echo ========================================
echo    GHOSTHUD WINDOWS - STARTING
echo ========================================
echo.
echo [*] Script location: %SCRIPT_DIR%
echo [*] Master IP: %MASTER_IP%
echo [*] Port: 7891
echo.

REM Start Windows peer
echo [*] Starting GhostHUD server...
echo.

python "%SCRIPT_DIR%windows.py" %MASTER_IP%

echo.
echo [!] Server stopped. Press any key to exit...
pause >nul

