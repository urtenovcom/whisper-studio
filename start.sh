#!/usr/bin/env bash
cd "$(dirname "$0")"
echo "============================================"
echo "  Whisper Studio - запуск"
echo "============================================"
echo
echo "[1/2] Проверка зависимостей..."
python3 -m pip install -r requirements.txt
echo
echo "[2/2] Запуск сервера..."
python3 app.py
