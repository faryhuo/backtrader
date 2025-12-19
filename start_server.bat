@echo off
chcp 65001 >nul 2>&1
setlocal

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%backend" || exit /b 1

if "%PORT%"=="" set "PORT=8000"
if "%LOG_LEVEL%"=="" set "LOG_LEVEL=INFO"
echo Starting FastAPI server on port %PORT% with log level %LOG_LEVEL%...
python main.py

endlocal
