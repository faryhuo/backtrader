@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%backend" || exit /b 1

if "%PORT%"=="" set "PORT=8000"
echo Starting FastAPI server on port %PORT%...
python -m uvicorn api:app --host 0.0.0.0 --port %PORT%

endlocal
