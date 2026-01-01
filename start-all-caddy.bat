@echo off
echo ========================================
echo   STARTING PROJECT WITH CADDY
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

echo Starting Next.js app (production)...
start "Next.js App" cmd /k "npm run start"
echo.

echo Waiting for Next.js to start (5 seconds)...
timeout /t 5 /nobreak >nul
echo.

echo Starting Caddy...
start "Caddy" cmd /k "caddy.exe run --config Caddyfile"
echo.

echo Waiting for Caddy to start (3 seconds)...
timeout /t 3 /nobreak >nul
echo.

echo Starting Telegram bot...
start "Telegram Bot" cmd /k start-bot.bat
echo.

echo ========================================
echo   ALL STARTED!
echo ========================================
echo.
echo Next.js: http://localhost:3000
echo Caddy: https://starscheckerahahqhq.site
echo Telegram Bot: Check third window
echo.
echo To stop, close all terminal windows
echo ========================================
echo.
pause
