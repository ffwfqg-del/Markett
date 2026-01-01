@echo off
echo ========================================
echo   ЗАПУСК ВСЕГО ПРОЕКТА
echo ========================================
echo.
echo Запускаю веб-приложение...
start "Web App" cmd /k start-webapp.bat
echo.
timeout /t 3 /nobreak >nul
echo Запускаю бота...
start "Telegram Bot" cmd /k start-bot.bat
echo.
echo ========================================
echo   ВСЁ ЗАПУЩЕНО!
echo ========================================
echo.
echo Web App: http://localhost:3000
echo Telegram Bot: Проверьте второе окно
echo.
echo Для остановки закройте оба окна терминала
echo ========================================
pause

