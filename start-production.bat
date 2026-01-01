@echo off
chcp 65001 >nul
echo ========================================
echo   ЗАПУСК В PRODUCTION РЕЖИМЕ
echo ========================================
echo.

REM Проверка зависимостей
if not exist "node_modules\" (
    echo Установка зависимостей...
    call npm install
    if errorlevel 1 (
        echo [ОШИБКА] Ошибка установки зависимостей!
        pause
        exit /b 1
    )
    echo.
)

REM Сборка приложения
echo Сборка приложения для production...
call npm run build
if errorlevel 1 (
    echo [ОШИБКА] Ошибка сборки приложения!
    pause
    exit /b 1
)
echo.

REM Установка переменной окружения
set NODE_ENV=production

echo ========================================
echo   ПРИЛОЖЕНИЕ СОБРАНО!
echo ========================================
echo.
echo Запуск production сервера...
echo Приложение будет доступно на http://localhost:3000
echo.
echo Для остановки нажмите Ctrl+C
echo ========================================
echo.

REM Запуск production сервера
npm run start

pause

