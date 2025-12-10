@echo off
echo ==========================================
echo Backtrader + Logto Configuration Check
echo ==========================================
echo.

echo [1/5] Checking backend .env file...
if exist "backend\.env" (
    echo ✓ backend\.env exists
    findstr /C:"LOGTO_ENDPOINT" backend\.env >nul
    if errorlevel 1 (
        echo ✗ LOGTO_ENDPOINT not found in backend\.env
    ) else (
        echo ✓ LOGTO_ENDPOINT configured
    )
    findstr /C:"LOGTO_APP_ID" backend\.env >nul
    if errorlevel 1 (
        echo ✗ LOGTO_APP_ID not found in backend\.env
    ) else (
        echo ✓ LOGTO_APP_ID configured
    )
    findstr /C:"LOGTO_AUDIENCE" backend\.env >nul
    if errorlevel 1 (
        echo ✗ LOGTO_AUDIENCE not found in backend\.env
    ) else (
        echo ✓ LOGTO_AUDIENCE configured
    )
) else (
    echo ✗ backend\.env does not exist
)
echo.

echo [2/5] Checking frontend .env file...
if exist "frontend\.env" (
    echo ✓ frontend\.env exists
    findstr /C:"VITE_LOGTO_ENDPOINT" frontend\.env >nul
    if errorlevel 1 (
        echo ✗ VITE_LOGTO_ENDPOINT not found in frontend\.env
    ) else (
        echo ✓ VITE_LOGTO_ENDPOINT configured
    )
    findstr /C:"VITE_LOGTO_APP_ID" frontend\.env >nul
    if errorlevel 1 (
        echo ✗ VITE_LOGTO_APP_ID not found in frontend\.env
    ) else (
        echo ✓ VITE_LOGTO_APP_ID configured
    )
    findstr /C:"VITE_API_RESOURCE" frontend\.env >nul
    if errorlevel 1 (
        echo ✗ VITE_API_RESOURCE not found in frontend\.env
    ) else (
        echo ✓ VITE_API_RESOURCE configured
    )
) else (
    echo ✗ frontend\.env does not exist
)
echo.

echo [3/5] Checking frontend build...
if exist "backend\resources\frontend\index.html" (
    echo ✓ Frontend build found in backend/resources/frontend/
) else (
    echo ✗ Frontend build not found. Run: build.bat
)
echo.

echo [4/5] Checking Python dependencies...
python -c "import jose" 2>nul
if errorlevel 1 (
    echo ✗ python-jose not installed. Run: pip install -r backend/requirements.txt
) else (
    echo ✓ python-jose installed
)

python -c "import requests" 2>nul
if errorlevel 1 (
    echo ✗ requests not installed. Run: pip install -r backend/requirements.txt
) else (
    echo ✓ requests installed
)
echo.

echo [5/5] Configuration values...
echo.
echo Backend Configuration:
type backend\.env | findstr /C:"LOGTO_ENDPOINT" /C:"LOGTO_APP_ID" /C:"LOGTO_AUDIENCE"
echo.
echo Frontend Configuration:
type frontend\.env | findstr /C:"VITE_LOGTO_ENDPOINT" /C:"VITE_LOGTO_APP_ID" /C:"VITE_API_RESOURCE" /C:"VITE_LOGTO_REDIRECT_URI"
echo.

echo ==========================================
echo Configuration Check Complete
echo ==========================================
echo.
echo IMPORTANT: Make sure in Logto Console:
echo 1. Frontend SPA app (ro4uk4fd2czd7cyx3wcbm) has:
echo    - Redirect URI: http://localhost:8000/callback
echo    - Post Logout URI: http://localhost:8000
echo    - CORS Origins: http://localhost:8000
echo    - API Resource linked: http://localhost:8000
echo.
echo 2. API Resource exists with identifier: http://localhost:8000
echo.
echo Next step: cd backend ^&^& python main.py
echo Then visit: http://localhost:8000
echo.
pause
