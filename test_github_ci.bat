@echo off
chcp 65001 >nul 2>&1
setlocal EnableExtensions

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
cd /d "%ROOT%"

set "WORKFLOW=.github\workflows\ci.yml"
set "CHECK_ONLY=0"
set "SKIP_INSTALL=0"
set "BACKEND_ENABLED=1"
set "FRONTEND_ENABLED=1"

:parse_args
if "%~1"=="" goto after_args
if /I "%~1"=="--check-only" (
  set "CHECK_ONLY=1"
  shift
  goto parse_args
)
if /I "%~1"=="--skip-install" (
  set "SKIP_INSTALL=1"
  shift
  goto parse_args
)
if /I "%~1"=="--backend-only" (
  set "BACKEND_ENABLED=1"
  set "FRONTEND_ENABLED=0"
  shift
  goto parse_args
)
if /I "%~1"=="--frontend-only" (
  set "BACKEND_ENABLED=0"
  set "FRONTEND_ENABLED=1"
  shift
  goto parse_args
)
if /I "%~1"=="--help" goto usage
if /I "%~1"=="-h" goto usage

echo Unknown argument: %~1
echo.
goto usage

:after_args
echo [INFO] Root: %ROOT%
echo [INFO] Workflow: %WORKFLOW%
echo.

if not exist "%WORKFLOW%" (
  echo [ERROR] Missing workflow file: %WORKFLOW%
  exit /b 1
)
echo [OK] Found workflow file: %WORKFLOW%

if not exist "backend\requirements.txt" (
  echo [ERROR] Missing backend requirements: backend\requirements.txt
  exit /b 1
)
echo [OK] Found backend requirements: backend\requirements.txt

if not exist "backend\requirements-dev.txt" (
  echo [ERROR] Missing backend dev requirements: backend\requirements-dev.txt
  exit /b 1
)
echo [OK] Found backend dev requirements: backend\requirements-dev.txt

if not exist "frontend\package.json" (
  echo [ERROR] Missing frontend package manifest: frontend\package.json
  exit /b 1
)
echo [OK] Found frontend package manifest: frontend\package.json

if not exist "frontend\package-lock.json" (
  echo [ERROR] Missing frontend lock file: frontend\package-lock.json
  exit /b 1
)
echo [OK] Found frontend lock file: frontend\package-lock.json

findstr /C:"name: CI" "%WORKFLOW%" >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Workflow is missing workflow name.
  exit /b 1
)
echo [OK] Workflow contains workflow name.

findstr /C:"backend-tests:" "%WORKFLOW%" >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Workflow is missing backend job.
  exit /b 1
)
echo [OK] Workflow contains backend job.

findstr /C:"frontend-lint:" "%WORKFLOW%" >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Workflow is missing frontend job.
  exit /b 1
)
echo [OK] Workflow contains frontend job.

findstr /C:"python-version:" "%WORKFLOW%" >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Workflow is missing python version key.
  exit /b 1
)
echo [OK] Workflow contains python version key.

findstr /C:"3.11" "%WORKFLOW%" >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Workflow is missing python version value.
  exit /b 1
)
echo [OK] Workflow contains python version value.

findstr /C:"node-version:" "%WORKFLOW%" >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Workflow is missing node version key.
  exit /b 1
)
echo [OK] Workflow contains node version key.

findstr /C:"20" "%WORKFLOW%" >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Workflow is missing node version value.
  exit /b 1
)
echo [OK] Workflow contains node version value.

findstr /C:"pytest --cov=src --cov-report=term-missing --cov-report=xml" "%WORKFLOW%" >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Workflow is missing backend test command.
  exit /b 1
)
echo [OK] Workflow contains backend test command.

findstr /C:"npm run lint" "%WORKFLOW%" >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Workflow is missing frontend lint command.
  exit /b 1
)
echo [OK] Workflow contains frontend lint command.

findstr /C:"\"lint\"" "frontend\package.json" >nul 2>&1
if errorlevel 1 (
  echo [ERROR] frontend\package.json does not define a lint script.
  exit /b 1
)
echo [OK] frontend\package.json contains a lint script.

if "%CHECK_ONLY%"=="1" (
  echo.
  echo [OK] Static workflow checks passed.
  exit /b 0
)

if "%BACKEND_ENABLED%"=="1" (
  call :run_backend
  if errorlevel 1 exit /b 1
)

if "%FRONTEND_ENABLED%"=="1" (
  call :run_frontend
  if errorlevel 1 exit /b 1
)

echo.
echo [OK] Local CI verification finished successfully.
exit /b 0

:run_backend
echo.
echo [STEP] Backend job
pushd "%ROOT%\backend" || (
  echo [ERROR] Failed to enter backend directory.
  exit /b 1
)

where python >nul 2>&1
if errorlevel 1 (
  echo [ERROR] python was not found in PATH.
  popd
  exit /b 1
)

python --version
if errorlevel 1 (
  echo [ERROR] Failed to query python version.
  popd
  exit /b 1
)

if not "%SKIP_INSTALL%"=="1" (
  echo [RUN] python -m pip install --upgrade pip
  python -m pip install --upgrade pip || (
    echo [ERROR] pip upgrade failed.
    popd
    exit /b 1
  )

  echo [RUN] pip install -r requirements.txt
  pip install -r requirements.txt || (
    echo [ERROR] backend dependency install failed.
    popd
    exit /b 1
  )

  echo [RUN] pip install -r requirements-dev.txt
  pip install -r requirements-dev.txt || (
    echo [ERROR] backend dev dependency install failed.
    popd
    exit /b 1
  )
) else (
  echo [INFO] Skipping backend dependency installation.
)

echo [RUN] python -m pytest --cov=src --cov-report=term-missing --cov-report=xml
python -m pytest --cov=src --cov-report=term-missing --cov-report=xml || (
  echo [ERROR] Backend tests failed.
  popd
  exit /b 1
)

if not exist "coverage.xml" (
  echo [ERROR] coverage.xml was not generated.
  popd
  exit /b 1
)

echo [OK] Backend job passed.
popd
exit /b 0

:run_frontend
echo.
echo [STEP] Frontend job
pushd "%ROOT%\frontend" || (
  echo [ERROR] Failed to enter frontend directory.
  exit /b 1
)

where npm >nul 2>&1
if errorlevel 1 (
  echo [ERROR] npm was not found in PATH.
  popd
  exit /b 1
)

node --version
if errorlevel 1 (
  echo [ERROR] Failed to query node version.
  popd
  exit /b 1
)

call npm --version
if errorlevel 1 (
  echo [ERROR] Failed to query npm version.
  popd
  exit /b 1
)

if not "%SKIP_INSTALL%"=="1" (
  echo [RUN] npm ci
  call npm ci || (
    echo [ERROR] npm ci failed.
    popd
    exit /b 1
  )
) else (
  echo [INFO] Skipping frontend dependency installation.
)

echo [RUN] npm run lint
call npm run lint || (
  echo [ERROR] Frontend lint failed.
  popd
  exit /b 1
)

echo [OK] Frontend job passed.
popd
exit /b 0

:usage
echo Usage: test_github_ci.bat [--check-only] [--skip-install] [--backend-only^|--frontend-only]
echo.
echo   --check-only    Only validate workflow structure and referenced files.
echo   --skip-install  Skip pip/npm install steps and run existing environments only.
echo   --backend-only  Only run the backend part of the workflow.
echo   --frontend-only Only run the frontend part of the workflow.
exit /b 1
