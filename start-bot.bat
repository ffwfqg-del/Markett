@echo off
echo ========================================
echo   ЗАПУСК TELEGRAM БОТА
echo ========================================
echo.
cd scripts
echo Проверка зависимостей Python...
python -c "import aiogram" 2>nul
if errorlevel 1 (
    echo Зависимости не найдены. Устанавливаю...
    pip install -r requirements.txt
)
echo.
echo Запуск бота...
echo Для остановки нажмите Ctrl+C
echo ========================================
echo.
python unified_bot_v3.py
pause

