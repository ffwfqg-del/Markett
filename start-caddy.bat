@echo off
chcp 65001 >nul
echo ========================================
echo   ЗАПУСК ПРИЛОЖЕНИЯ С CADDY
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

REM Проверка наличия Caddyfile
if not exist "Caddyfile" (
    echo [ОШИБКА] Файл Caddyfile не найден!
    echo.
    pause
    exit /b 1
)

echo Запуск Next.js приложения...
start "Next.js App" cmd /k "npm run start"
echo.

REM Ожидание запуска Next.js
echo Ожидание запуска Next.js (5 секунд)...
timeout /t 5 /nobreak >nul
echo.

echo Запуск Caddy...
echo.
echo ========================================
echo   ВСЁ ЗАПУЩЕНО!
echo ========================================
echo.
echo Next.js: http://localhost:3000
echo Caddy: Проверьте ваш домен в браузере
echo.
echo Для остановки закройте оба окна терминала
echo ========================================
echo.

REM Запуск Caddy
caddy.exe run --config Caddyfile

pause

