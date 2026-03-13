@echo off
REM Windows Diagnostic Script - Check if OMNI is actually running

echo ======================================================================
echo   OMNI WINDOWS DIAGNOSTIC
echo ======================================================================
echo.

echo [1] Checking if Python processes are running...
tasklist /FI "IMAGENAME eq python.exe" 2>nul | find /I "python.exe" >nul
if %ERRORLEVEL% == 0 (
    echo   ✅ Python processes found
    tasklist /FI "IMAGENAME eq python.exe" | findstr python
) else (
    echo   ❌ NO Python processes running!
    echo   → Servers are NOT running
    echo   → Run launch_omni_windows.bat first
    goto :end
)

echo.
echo [2] Checking if ports 8888 and 8889 are listening...
netstat -an | findstr ":8888" >nul
if %ERRORLEVEL% == 0 (
    echo   ✅ Port 8888 is LISTENING
    netstat -an | findstr ":8888"
) else (
    echo   ❌ Port 8888 is NOT listening
)

netstat -an | findstr ":8889" >nul
if %ERRORLEVEL% == 0 (
    echo   ✅ Port 8889 is LISTENING
    netstat -an | findstr ":8889"
) else (
    echo   ❌ Port 8889 is NOT listening
)

echo.
echo [3] Testing if servers respond...
echo   Testing http://127.0.0.1:8888...
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://127.0.0.1:8888' -TimeoutSec 2 -UseBasicParsing; Write-Host '   ✅ Server RESPONDED (Status:' $response.StatusCode ')' } catch { Write-Host '   ❌ Server NOT responding:' $_.Exception.Message }"

echo   Testing http://127.0.0.1:8889...
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://127.0.0.1:8889' -TimeoutSec 2 -UseBasicParsing; Write-Host '   ✅ Server RESPONDED (Status:' $response.StatusCode ')' } catch { Write-Host '   ❌ Server NOT responding:' $_.Exception.Message }"

echo.
echo [4] Checking Windows Firewall...
netsh advfirewall firewall show rule name=all | findstr /I "8888 8889 python" >nul
if %ERRORLEVEL% == 0 (
    echo   ⚠️  Firewall rules found (may need to allow Python)
) else (
    echo   ⚠️  No firewall rules found for ports 8888/8889
    echo   → Windows Firewall may be blocking
)

echo.
echo ======================================================================
echo   DIAGNOSTIC COMPLETE
echo ======================================================================
echo.
echo If servers are NOT responding:
echo   1. Check if Python processes are running (step 1)
echo   2. Check if ports are listening (step 2)
echo   3. If ports not listening, servers didn't start properly
echo   4. Try running launch_omni_windows.bat again
echo.
echo If ports ARE listening but not responding:
echo   → Windows Firewall is blocking
echo   → Allow Python through firewall
echo.
pause

:end
