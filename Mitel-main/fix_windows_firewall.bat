@echo off
REM Quick fix for Windows Firewall - Allow Python and ports 8888/8889

echo ======================================================================
echo   WINDOWS FIREWALL FIX
echo ======================================================================
echo.
echo This will add firewall rules to allow OMNI servers...
echo.

REM Add firewall rule for port 8888
netsh advfirewall firewall add rule name="OMNI Operations Console" dir=in action=allow protocol=TCP localport=8888
if %ERRORLEVEL% == 0 (
    echo ✅ Added firewall rule for port 8888
) else (
    echo ❌ Failed to add firewall rule (may need admin rights)
)

REM Add firewall rule for port 8889
netsh advfirewall firewall add rule name="OMNI AI Chat" dir=in action=allow protocol=TCP localport=8889
if %ERRORLEVEL% == 0 (
    echo ✅ Added firewall rule for port 8889
) else (
    echo ❌ Failed to add firewall rule (may need admin rights)
)

REM Add firewall rule for Python
netsh advfirewall firewall add rule name="Python OMNI" dir=in action=allow program="%PYTHON%" enable=yes
if %ERRORLEVEL% == 0 (
    echo ✅ Added firewall rule for Python
) else (
    echo ⚠️  Could not add Python rule (may need full path)
)

echo.
echo ======================================================================
echo   FIREWALL RULES ADDED
echo ======================================================================
echo.
echo If you got errors, you may need to:
echo   1. Right-click this file
echo   2. Select "Run as administrator"
echo.
echo Now try accessing:
echo   http://127.0.0.1:8888
echo   http://127.0.0.1:8889
echo.
pause
