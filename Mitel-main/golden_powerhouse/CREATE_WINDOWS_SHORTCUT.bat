@echo off
REM Create Windows Desktop Shortcut for GhostHUD
REM This should be run from the extracted directory

setlocal

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"
set "DESKTOP=%USERPROFILE%\Desktop"

REM Create VBScript to create shortcut
set "VBS=%TEMP%\create_shortcut.vbs"
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%VBS%"
echo sLinkFile = "%DESKTOP%\GhostHUD.lnk" >> "%VBS%"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%VBS%"
echo oLink.TargetPath = "%SCRIPT_DIR%START_GHOSTHUD.bat" >> "%VBS%"
echo oLink.WorkingDirectory = "%SCRIPT_DIR%" >> "%VBS%"
echo oLink.Description = "Nexian Omni Quantum Compute GhostOps Engine" >> "%VBS%"
echo oLink.IconLocation = "shell32.dll,1" >> "%VBS%"
echo oLink.Save >> "%VBS%"

REM Run VBScript
cscript //nologo "%VBS%"

REM Cleanup
del "%VBS%"

echo.
echo [*] Desktop shortcut created: %DESKTOP%\GhostHUD.lnk
echo [*] Double-click "GhostHUD" on your desktop to launch!
echo.
pause

