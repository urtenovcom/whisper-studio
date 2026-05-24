@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   Whisper Studio - запуск
echo ============================================
echo.
echo [1/2] Проверка зависимостей...
python -m pip install -r requirements.txt
echo.
echo [2/2] Запуск сервера...
python app.py
pause
