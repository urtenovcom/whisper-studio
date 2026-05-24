@echo off
setlocal
cd /d "%~dp0"

set PROG=%~dp0setup.progress
set DONE=%~dp0setup.done

>"%PROG%" echo 5^|Подготовка пакетного менеджера...
python\python.exe get-pip.py --no-warn-script-location --disable-pip-version-check --quiet
if errorlevel 1 goto :error

>"%PROG%" echo 12^|Установка ядра: FastAPI, Whisper, Sherpa...
python\python.exe -m pip install --no-warn-script-location --disable-pip-version-check --no-cache-dir --quiet ^
  "fastapi==0.115.6" "uvicorn[standard]==0.34.0" "python-multipart==0.0.20" ^
  "faster-whisper==1.1.1" "python-docx==1.1.2" "sherpa-onnx==1.13.2"
if errorlevel 1 goto :error

>"%PROG%" echo 35^|Установка интерфейса (PySide6)...
python\python.exe -m pip install --no-warn-script-location --disable-pip-version-check --no-cache-dir --quiet "PySide6==6.11.1"
if errorlevel 1 goto :error

>"%PROG%" echo 55^|Установка модулей диктовки...
python\python.exe -m pip install --no-warn-script-location --disable-pip-version-check --no-cache-dir --quiet ^
  "pynput==1.8.2" "sounddevice==0.5.5" "pyperclip==1.11.0" "requests==2.34.2"
if errorlevel 1 goto :error

>"%PROG%" echo 65^|Загрузка библиотек NVIDIA (самая тяжёлая часть, ~1 ГБ)...
python\python.exe -m pip install --no-warn-script-location --disable-pip-version-check --no-cache-dir --quiet ^
  "nvidia-cublas-cu12==12.9.2.10" "nvidia-cudnn-cu12==9.22.0.52"
if errorlevel 1 goto :error

>"%PROG%" echo 95^|Завершение...
>"%DONE%" echo done
exit /b 0

:error
>"%PROG%" echo 0^|Ошибка установки
>"%DONE%" echo error
exit /b 1
