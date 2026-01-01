@echo off
chcp 65001 >nul
title Telegram Bot v3.0
color 0A

echo ========================================
echo    TELEGRAM BOT v3.0
echo ========================================
echo.

cd /d "%~dp0"

echo [INFO] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo [ERROR] Please install Python 3.11+ and add it to PATH
    pause
    exit /b 1
)

echo [INFO] Python found!
python --version
echo.

echo [INFO] Checking settings.json...
if not exist "settings.json" (
    echo [ERROR] settings.json not found!
    echo [ERROR] Please create settings.json with your configuration
    pause
    exit /b 1
)

echo [INFO] Starting bot...
echo.

python unified_bot_v3.py

if errorlevel 1 (
    echo.
    echo [ERROR] Bot crashed! Check the error above.
    pause
)

