@echo off
echo ========================================
echo   ЗАПУСК ВЕБ-ПРИЛОЖЕНИЯ (Next.js)
echo ========================================
echo.
echo Проверка зависимостей...
if not exist "node_modules\" (
    echo Зависимости не найдены. Устанавливаю...
    call npm install
)
echo.
echo Запуск сервера разработки...
echo Сайт будет доступен по адресу: http://localhost:3000
echo.
echo Для остановки нажмите Ctrl+C
echo ========================================
echo.
call npm run dev
pause

