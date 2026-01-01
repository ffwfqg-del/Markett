@echo off
echo ========================================
echo   STARTING PRODUCTION MODE
echo ========================================
echo.

REM Check dependencies
if not exist "node_modules\" (
    echo Installing dependencies...
    call npm install
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies!
        pause
        exit /b 1
    )
    echo.
)

REM Build app
echo Building app for production...
call npm run build
if errorlevel 1 (
    echo [ERROR] Build failed!
    pause
    exit /b 1
)
echo.

REM Set environment variable
set NODE_ENV=production

echo ========================================
echo   APP BUILT!
echo ========================================
echo.
echo Starting production server...
echo App will be available at http://localhost:3000
echo.
echo Press Ctrl+C to stop
echo ========================================
echo.

REM Start production server
npm run start

pause

