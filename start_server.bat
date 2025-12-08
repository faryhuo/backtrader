@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%backend" || exit /b 1

if "%PORT%"=="" set "PORT=8000"
echo Starting FastAPI server on port %PORT%...
python main.py

endlocal
