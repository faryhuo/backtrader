@echo off
chcp 65001 >nul 2>&1
setlocal

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

if not exist "%ROOT%\backend" (
    echo Backend directory not found at "%ROOT%\backend".
    exit /b 1
)
if not exist "%ROOT%\frontend" (
    echo Frontend directory not found at "%ROOT%\frontend".
    exit /b 1
)

start "backtrader-backend" cmd /k "cd /d ""%ROOT%\backend"" && python main.py || (echo Backend process exited. Press any key to close... & pause)"

start "backtrader-frontend" cmd /k "cd /d ""%ROOT%\frontend"" && npm run dev || (echo Frontend process exited. Press any key to close... & pause)"

echo Launching backend (port 8000) and frontend dev server (default Vite port 5173)...
echo Two terminal windows should open; check them for logs and errors.

endlocal
