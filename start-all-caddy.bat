@echo off
chcp 65001 >nul
echo ========================================
echo   ЗАПУСК ВСЕГО ПРОЕКТА С CADDY
echo ========================================
echo.

REM Проверка наличия Caddy
if not exist "caddy.exe" (
    echo [ОШИБКА] Файл caddy.exe не найден!
    echo.
    echo Скачайте Caddy с https://caddyserver.com/download
    echo Переименуйте файл в caddy.exe и поместите в эту папку
    echo.
    pause
    exit /b 1
)

REM Проверка наличия собранного приложения
if not exist ".next" (
    echo [ПРЕДУПРЕЖДЕНИЕ] Приложение не собрано!
    echo Собираю приложение...
    call npm run build
    if errorlevel 1 (
        echo [ОШИБКА] Ошибка сборки приложения!
        pause
        exit /b 1
    )
    echo.
)

REM Создание папки для логов
if not exist "logs" mkdir logs

echo Запуск Next.js приложения (production)...
start "Next.js App" cmd /k "npm run start"
echo.

echo Ожидание запуска Next.js (5 секунд)...
timeout /t 5 /nobreak >nul
echo.

echo Запуск Caddy...
start "Caddy" cmd /k "caddy.exe run --config Caddyfile"
echo.

echo Ожидание запуска Caddy (3 секунды)...
timeout /t 3 /nobreak >nul
echo.

echo Запуск Telegram бота...
start "Telegram Bot" cmd /k start-bot.bat
echo.

echo ========================================
echo   ВСЁ ЗАПУЩЕНО!
echo ========================================
echo.
echo Next.js: http://localhost:3000
echo Caddy: https://starscheckerahahqhq.site
echo Telegram Bot: Проверьте третье окно
echo.
echo Для остановки закройте все окна терминала
echo ========================================
echo.
pause

