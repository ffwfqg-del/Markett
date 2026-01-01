@echo off
echo ========================================
echo   STARTING APP WITH CADDY
echo ========================================
echo.

REM Check if dependencies are installed
if not exist "node_modules\" (
    echo [WARNING] Dependencies not installed! Installing now...
    call npm install
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies!
        pause
        exit /b 1
    )
    echo.
)

REM Check if Caddy exists
if not exist "caddy.exe" (
    echo [ERROR] caddy.exe not found!
    echo.
    echo Download Caddy from https://caddyserver.com/download
    echo Rename to caddy.exe and place in this folder
    echo.
    pause
    exit /b 1
)

REM Check if app is built
if not exist ".next" (
    echo [WARNING] App not built! Building now...
    call npm run build
    if errorlevel 1 (
        echo [ERROR] Build failed!
        pause
        exit /b 1
    )
    echo.
)

REM Create logs folder
if not exist "logs" mkdir logs

REM Check if Caddyfile exists
if not exist "Caddyfile" (
    echo [ERROR] Caddyfile not found!
    echo.
    pause
    exit /b 1
)

echo Starting Next.js app...
start "Next.js App" cmd /k "npm run start"
echo.

REM Wait for Next.js
echo Waiting for Next.js to start (5 seconds)...
timeout /t 5 /nobreak >nul
echo.

echo Starting Caddy...
echo.
echo ========================================
echo   ALL STARTED!
echo ========================================
echo.
echo Next.js: http://localhost:3000
echo Caddy: Check your domain in browser
echo.
echo To stop, close both terminal windows
echo ========================================
echo.

REM Start Caddy
caddy.exe run --config Caddyfile

pause
