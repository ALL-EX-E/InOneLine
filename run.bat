@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

if not exist "logs" mkdir "logs"
set "LOG=%~dp0logs\startup.log"

> "%LOG%" echo ==== In one line startup ====
>> "%LOG%" echo Date: %date% %time%
>> "%LOG%" echo Folder: %cd%

echo.
echo ==============================================
echo        In one line - startup
echo ==============================================
echo.

REM Reuse the local virtual environment when it already exists.
if exist ".venv\Scripts\python.exe" goto INSTALL_CHECK

REM Prefer the Windows Python launcher when available.
py -3 -c "import sys; print(sys.executable)" >nul 2>&1
if not errorlevel 1 goto USE_PY

REM Fall back to python.exe. This also rejects a non-working Store alias.
python -c "import sys; print(sys.executable)" >nul 2>&1
if not errorlevel 1 goto USE_PYTHON

echo [ERROR] A working Python 3 installation was not found.
echo.
echo Install Python 3.12 x64 and then run this file again.
echo Recommended command:
echo.
echo   winget install -e --id Python.Python.3.12
echo.
echo If winget is unavailable, install Python 3 x64 from python.org
echo and enable "Add python.exe to PATH" during installation.
echo.
>> "%LOG%" echo ERROR: Working Python 3 not found.
pause
exit /b 1

:USE_PY
set "PY_CMD=py -3"
goto CREATE_VENV

:USE_PYTHON
set "PY_CMD=python"
goto CREATE_VENV

:CREATE_VENV
echo Python found. Creating local .venv...
>> "%LOG%" echo Python command: %PY_CMD%
%PY_CMD% --version >> "%LOG%" 2>&1
%PY_CMD% -m venv ".venv" >> "%LOG%" 2>&1
if errorlevel 1 goto VENV_ERROR

:INSTALL_CHECK
echo Checking dependencies...
".venv\Scripts\python.exe" -c "import PySide6, openpyxl, websocket" >nul 2>&1
if not errorlevel 1 goto RUN_APP

echo.
echo First start: installing required components.
echo This can take several minutes and requires Internet access.
echo.
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto PIP_ERROR

".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto PIP_ERROR

:RUN_APP
echo.
echo Starting In one line...
echo.
".venv\Scripts\python.exe" app.py 2>> "%LOG%"
set "APP_CODE=%ERRORLEVEL%"
if "%APP_CODE%"=="0" exit /b 0

echo.
echo [ERROR] Application exited with code %APP_CODE%.
echo.
echo Startup log:
type "%LOG%"
echo.
echo Additional diagnostics may be stored in:
echo %~dp0logs\startup_error.log
pause
exit /b %APP_CODE%

:VENV_ERROR
echo.
echo [ERROR] Could not create .venv.
echo.
type "%LOG%"
echo.
pause
exit /b 2

:PIP_ERROR
echo.
echo [ERROR] Could not install dependencies.
echo.
echo Python version:
".venv\Scripts\python.exe" --version
echo.
echo Startup log:
type "%LOG%"
echo.
pause
exit /b 3
