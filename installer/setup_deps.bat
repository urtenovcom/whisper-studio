@echo off
setlocal
cd /d "%~dp0"

title Whisper Studio - установка зависимостей
mode con cols=110 lines=30
color 0B

echo ============================================================
echo   Whisper Studio - установка
echo   Это разовая операция, занимает 5-10 минут.
echo   Не закрывайте это окно!
echo ============================================================
echo.

echo [1/2] Настройка пакетного менеджера...
python\python.exe get-pip.py --no-warn-script-location --disable-pip-version-check 2>&1 | findstr /V "^$"
if errorlevel 1 goto :error

echo.
echo [2/2] Загрузка библиотек с PyPI (около 1.5 ГБ)...
echo.
python\python.exe -m pip install --no-warn-script-location --disable-pip-version-check --no-cache-dir --progress-bar on -r requirements-runtime.txt
if errorlevel 1 goto :error

echo.
echo ============================================================
echo   Готово! Запускаю Whisper Studio...
echo ============================================================
ping -n 3 127.0.0.1 >nul
exit /b 0

:error
echo.
echo ============================================================
echo   ОШИБКА: установка не завершилась.
echo   Проверьте подключение к интернету и запустите установку заново.
echo ============================================================
echo.
echo Нажмите любую клавишу...
pause >nul
exit /b 1
