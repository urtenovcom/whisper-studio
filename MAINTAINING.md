# Сборка и выпуск релизов

Заметки для мейнтейнера. Не отображается в основном README.

## Сборка установщика

```powershell
# 1. Перегенерировать иконку (если правили mainwindow.py:make_app_icon)
.venv\Scripts\python.exe installer\make_ico.py installer\app.ico

# 2. Скомпилировать через Inno Setup
"$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe" installer\whisper-studio.iss
```

Результат: `dist-installer\WhisperStudio-Setup.exe`

## Выпуск нового релиза

1. Поднять `APP_VERSION` в `app.py`.
2. Пересобрать установщик (см. выше).
3. Закоммитить и запушить.
4. Создать релиз на GitHub:
   ```powershell
   gh release create vX.Y dist-installer\WhisperStudio-Setup.exe `
     --title "Whisper Studio X.Y" `
     --notes "Что изменилось в этой версии"
   ```

После публикации релиза:
- При следующем запуске или через 6 часов у пользователей появится
  кнопка «Обновить → vX.Y» в нижнем левом углу.
- Клик → скачивание `Setup.exe` → тихая переустановка → авто-перезапуск.

## Где живут модели

- **Диаризация:** комплектные `segmentation.onnx` + `embedding.onnx` лежат
  в `data/models/diarize/`. Включены в установщик через `[Files]` секцию `.iss`.
- **Whisper:** качаются автоматически с HuggingFace при первом использовании,
  кэш в `%USERPROFILE%\.cache\huggingface\`.

## Структура установленной программы

```
C:\Program Files\Whisper Studio\
├── python\              # Embeddable Python 3.14 + site-packages
├── static\              # Веб-интерфейс (HTML/CSS/JS)
├── resources\           # Звуки диктовки (.wav)
├── data\models\diarize\ # Модели определения говорящих
├── app.py               # Точка входа
├── dictation.py
├── mainwindow.py
├── overlay.py
├── app.ico
├── setup_deps.bat       # Используется только при установке
└── unins000.exe         # Деинсталлятор Inno Setup
```

Пользовательские данные отдельно: `%APPDATA%\Whisper Studio\`.
