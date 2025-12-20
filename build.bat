@echo off
chcp 65001 >nul 2>&1
setlocal

set "ROOT=%~dp0"

REM Activate virtual environment if exists
if exist "%ROOT%venv_new\Scripts\activate.bat" (
    echo Activating virtual environment...
    call "%ROOT%venv_new\Scripts\activate.bat"
) else (
    echo Warning: Virtual environment not found at venv_new\Scripts\
    echo Continuing with system Python...
)

cd /d "%ROOT%backend" || exit /b 1
echo Installing backend dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo Backend dependency install failed.
    exit /b 1
)

cd /d "%ROOT%frontend" || exit /b 1

echo Installing frontend dependencies...
call npm install
if errorlevel 1 (
    echo npm install failed.
    exit /b 1
)

echo Building frontend...
call npm run build
if errorlevel 1 (
    echo Frontend build failed.
    exit /b 1
)

set "DEST=%ROOT%backend\resources\frontend"
if not exist "%DEST%" mkdir "%DEST%"

echo Copying build artifacts to backend resources...
robocopy "%ROOT%frontend\dist" "%DEST%" /MIR >nul
set "RC=%ERRORLEVEL%"
if %RC% GEQ 8 (
    echo Copying files failed with code %RC%.
    exit /b %RC%
)

echo Build complete. Static files are in %DEST%.
endlocal
