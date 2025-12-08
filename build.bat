@echo off
setlocal

REM Determine repo root
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%" || exit /b 1

REM Default image tag; can override by passing tag as first argument
set "IMAGE_NAME=backtrader-app:latest"
if not "%~1"=="" set "IMAGE_NAME=%~1"

REM Optional pip mirror args for backend build
set "BUILD_ARGS="
if defined PIP_INDEX_URL set "BUILD_ARGS=%BUILD_ARGS% --build-arg PIP_INDEX_URL=%PIP_INDEX_URL%"
if defined PIP_TRUSTED_HOST set "BUILD_ARGS=%BUILD_ARGS% --build-arg PIP_TRUSTED_HOST=%PIP_TRUSTED_HOST%"

echo Building Docker image "%IMAGE_NAME%"...
docker build %BUILD_ARGS% -t "%IMAGE_NAME%" .
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" (
    echo Build failed with exit code %EXIT_CODE%.
    exit /b %EXIT_CODE%
)

echo Build complete.
endlocal
