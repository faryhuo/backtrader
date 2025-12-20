@echo off
chcp 65001 >nul
REM Auto Test Runner for Backtrader Project
REM Run automated tests with various options

setlocal

cd /d "%~dp0"

echo ========================================
echo   Backtrader Auto Test Runner
echo ========================================
echo.

REM Check if pytest is installed
python -c "import pytest" 2>nul
if errorlevel 1 (
    echo [ERROR] pytest is not installed!
    echo Please install test dependencies first:
    echo   pip install -r requirements.txt
    echo   playwright install chromium
    pause
    exit /b 1
)

REM Parse command line arguments
set TEST_TYPE=%1

if "%TEST_TYPE%"=="" (
    echo Usage: run_tests.bat [smoke^|e2e^|api^|ui^|all]
    echo.
    echo Options:
    echo   smoke  - Run smoke tests only (fast, ^<30s)
    echo   e2e    - Run all e2e tests
    echo   api    - Run API tests only
    echo   ui     - Run UI/browser tests only
    echo   all    - Run all tests (default)
    echo.
    set /p TEST_TYPE="Select test type (smoke/e2e/api/ui/all): "
)

if "%TEST_TYPE%"=="" set TEST_TYPE=smoke

REM Check if servers are running
echo.
echo [Pre-flight Check] Checking if servers are running...
echo.

REM Check backend
curl -s http://localhost:8000/api/strategies >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Backend server not responding on http://localhost:8000
    echo           API tests may fail. Start backend with: .\start_server.bat
) else (
    echo [OK] Backend server is responding on http://localhost:8000
)

REM Check frontend (only for UI tests)
if /i "%TEST_TYPE%"=="ui" (
    curl -s http://localhost:5173 >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] Frontend server not running on http://localhost:5173
        echo           UI tests will be skipped. Start frontend with: npm run dev
    ) else (
        echo [OK] Frontend server is responding on http://localhost:5173
    )
)

echo.
echo Running %TEST_TYPE% tests...
echo.

if /i "%TEST_TYPE%"=="smoke" (
    echo [Smoke Tests] Running critical health checks...
    python -m pytest -m smoke -v
    goto :end
)

if /i "%TEST_TYPE%"=="e2e" (
    echo [E2E Tests] Running end-to-end tests...
    python -m pytest e2e/ -v
    goto :end
)

if /i "%TEST_TYPE%"=="api" (
    echo [API Tests] Running API tests...
    python -m pytest -m api -v
    goto :end
)

if /i "%TEST_TYPE%"=="ui" (
    echo [UI Tests] Running browser tests...
    python -m pytest -m ui -v
    goto :end
)

if /i "%TEST_TYPE%"=="all" (
    echo [All Tests] Running complete test suite...
    python -m pytest -v
    goto :end
)

echo [ERROR] Invalid test type: %TEST_TYPE%
echo Valid options are: smoke, e2e, api, ui, all
exit /b 1

:end
echo.
echo ========================================
echo   Tests completed!
echo ========================================
pause
