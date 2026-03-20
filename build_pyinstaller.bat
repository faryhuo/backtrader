@echo off
chcp 65001 >nul 2>&1
setlocal EnableExtensions

set "ROOT=%~dp0"
set "APP_NAME=backtrader-server"
set "VENV_ACTIVATED="

if exist "%ROOT%venv_new\Scripts\activate.bat" (
    echo Activating virtual environment: venv_new
    call "%ROOT%venv_new\Scripts\activate.bat"
    set "VENV_ACTIVATED=1"
) else if exist "%ROOT%.venv\Scripts\activate.bat" (
    echo Activating virtual environment: .venv
    call "%ROOT%.venv\Scripts\activate.bat"
    set "VENV_ACTIVATED=1"
) else if exist "%ROOT%venv\Scripts\activate.bat" (
    echo Activating virtual environment: venv
    call "%ROOT%venv\Scripts\activate.bat"
    set "VENV_ACTIVATED=1"
)

if not defined VENV_ACTIVATED (
    echo Virtual environment not found. Using system Python.
)

where python >nul 2>&1
if errorlevel 1 (
    echo Python not found in PATH.
    exit /b 1
)

where npm >nul 2>&1
if errorlevel 1 (
    echo npm not found in PATH. Please install Node.js first.
    exit /b 1
)

echo.
echo [1/6] Installing backend dependencies and PyInstaller...
cd /d "%ROOT%backend" || exit /b 1
python -m pip install --upgrade pip
if errorlevel 1 exit /b 1
python -m pip install -r requirements.txt pyinstaller
if errorlevel 1 (
    echo Backend dependency installation failed.
    exit /b 1
)

echo.
echo [2/6] Building frontend...
cd /d "%ROOT%frontend" || exit /b 1
call npm install
if errorlevel 1 (
    echo npm install failed.
    exit /b 1
)
call npm run build
if errorlevel 1 (
    echo Frontend build failed.
    exit /b 1
)

echo.
echo [3/6] Syncing frontend assets into backend resources...
set "FRONTEND_DEST=%ROOT%backend\resources\frontend"
if not exist "%FRONTEND_DEST%" mkdir "%FRONTEND_DEST%"
robocopy "%ROOT%frontend\dist" "%FRONTEND_DEST%" /MIR >nul
set "ROBOCOPY_RC=%ERRORLEVEL%"
if %ROBOCOPY_RC% GEQ 8 (
    echo Frontend asset copy failed with code %ROBOCOPY_RC%.
    exit /b %ROBOCOPY_RC%
)

echo.
echo [4/6] Cleaning previous PyInstaller output...
if exist "%ROOT%build\%APP_NAME%" rmdir /s /q "%ROOT%build\%APP_NAME%"
if exist "%ROOT%dist\%APP_NAME%" rmdir /s /q "%ROOT%dist\%APP_NAME%"

echo.
echo [5/6] Building executable...
cd /d "%ROOT%" || exit /b 1
python -m PyInstaller --noconfirm --clean --distpath "%ROOT%dist" --workpath "%ROOT%build" "%ROOT%%APP_NAME%.spec"
if errorlevel 1 (
    echo PyInstaller build failed.
    exit /b 1
)

echo.
echo [6/6] Copying runtime resources beside the executable...
if not exist "%ROOT%dist\%APP_NAME%\resources" mkdir "%ROOT%dist\%APP_NAME%\resources"
robocopy "%ROOT%backend\resources" "%ROOT%dist\%APP_NAME%\resources" /E >nul
set "ROBOCOPY_RC=%ERRORLEVEL%"
if %ROBOCOPY_RC% GEQ 8 (
    echo Resource copy failed with code %ROBOCOPY_RC%.
    exit /b %ROBOCOPY_RC%
)

if exist "%ROOT%backend\.env.template" (
    copy /y "%ROOT%backend\.env.template" "%ROOT%dist\%APP_NAME%\.env.template" >nul
)

echo.
echo Build complete.
echo Executable directory: %ROOT%dist\%APP_NAME%
echo Startup file: %ROOT%dist\%APP_NAME%\%APP_NAME%.exe
echo.
echo Notes:
echo   1. First run can use .env.template as a base to create .env.
echo   2. Runtime data will be stored under dist\%APP_NAME%\resources and dist\%APP_NAME%\trading_sessions.db.
echo   3. In exe mode, isolated subprocess strategy validation falls back to in-process validation.

endlocal
