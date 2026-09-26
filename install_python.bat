@echo off
setlocal EnableExtensions
chcp 65001 >nul
echo.
echo Installing Python 3.12 x64 with Windows Package Manager.
echo.
where winget >nul 2>&1
if errorlevel 1 goto NO_WINGET
winget install -e --id Python.Python.3.12
echo.
echo After installation finishes, close this window and run run.bat again.
pause
exit /b 0

:NO_WINGET
echo [ERROR] winget was not found.
echo Install Python 3 x64 manually from python.org and enable
 echo "Add python.exe to PATH" during installation.
pause
exit /b 1
