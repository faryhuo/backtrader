@echo off
chcp 65001 >nul 2>&1
setlocal

REM Run pytest and generate coverage reports (terminal + HTML + XML).
REM Optional (first time):  python -m pip install -r requirements.txt -r requirements-dev.txt

cd /d "%~dp0"

python -m pytest -q ^
  --cov=src ^
  --cov-report=term-missing ^
  --cov-report=html:coverage_html ^
  --cov-report=xml:coverage.xml

set EXITCODE=%ERRORLEVEL%
if not "%EXITCODE%"=="0" (
  echo.
  echo Tests failed (exit code %EXITCODE%).
  exit /b %EXITCODE%
)

echo.
echo Coverage reports generated:
echo   - HTML: %CD%\coverage_html\index.html
echo   - XML : %CD%\coverage.xml
exit /b 0

