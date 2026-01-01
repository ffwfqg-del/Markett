@echo off
chcp 65001 >nul
title Install Bot Dependencies
color 0B

echo ========================================
echo    Installing Bot Dependencies
echo ========================================
echo.

cd /d "%~dp0"

echo [INFO] Upgrading pip...
python -m pip install --upgrade pip
echo.

echo [INFO] Installing dependencies from requirements.txt...
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [ERROR] Installation failed!
    pause
    exit /b 1
)

echo.
echo [SUCCESS] All dependencies installed!
echo.
pause

