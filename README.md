# Whisper Studio

Local audio transcription powered by **faster-whisper**.
Modern desktop interface, everything runs on your computer: no subscription,
no limits, no audio sent to third-party servers.

*Powered by Alazar Studio.*

---

## Installation

1. Download **`WhisperStudio-Setup.exe`** from the latest release:
   👉 [github.com/urtenovcom/whisper-studio/releases/latest](https://github.com/urtenovcom/whisper-studio/releases/latest)
2. Run the installer — Windows UAC confirmation required.
3. Setup takes 5–10 minutes (dependencies download from the internet once).
4. The app starts automatically when done. Shortcut goes to Desktop and Start menu.

> Windows 10/11 (x64) supported. macOS / Linux not in the installer yet, but
> the code is cross-platform — run manually (see below).

---

## Features

### Transcription
- Drag-and-drop audio/video upload
- Models: `small`, `medium`, `large-v3` (for Russian — `medium` or `large-v3`)
- Automatic **NVIDIA GPU** use (CUDA 12 / cuDNN 9 bundled with the installer)
- Batch processing with per-job cancel
- Player with timestamps, click on time to seek
- Inline editing (Enter — save, Esc — revert)
- Bookmarks on important lines
- Full-text search inside a transcript
- Export to **TXT, DOCX, SRT, VTT**

### Speaker recognition
- Works out of the box — **no HuggingFace account or tokens required**
- Optionally specify the exact number of speakers for much better quality
- Rename a speaker (Speaker 1 → Name) once — applied to all their lines
- Speaker chips above the transcript can be temporarily hidden

### Push-to-talk dictation
- Hold Right Ctrl (or any key/combo) — speak — release — text appears in active window
- Works anywhere (messengers, documents, browser)
- Start-of-recording chime, floating equalizer pill on top of all windows
- Configurable: hotkey, delay, model, language, microphone

### Storage
- **Projects (folders)** to group recordings, move between projects
- Search across all transcriptions
- All data stays local in `%APPDATA%\Whisper Studio\`

### Interface
- Light / dark / system theme
- Russian / English UI
- Minimizes to system tray on close (keeps running)
- Start with Windows (optional, in Settings)
- In-app auto-update via GitHub Releases

---

## Manual run (for developers)

To run from source or modify the code:

```bash
# Python 3.12 recommended (PyTorch CUDA wheels for 3.14 are not out yet)
python -m venv .venv
.venv\Scripts\activate         # Windows
# source .venv/bin/activate    # macOS/Linux

pip install -r requirements.txt
pip install PySide6 pynput sounddevice pyperclip requests
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12  # NVIDIA GPU only

python app.py
```

The app opens its own window (Qt WebEngine) and starts a local server at
`http://127.0.0.1:8756`.

---

## Data layout

| Folder | Contents |
|---|---|
| `%APPDATA%\Whisper Studio\recordings\` | transcriptions (JSON) |
| `%APPDATA%\Whisper Studio\uploads\` | original audio files |
| `%APPDATA%\Whisper Studio\projects.json` | project list |
| `%APPDATA%\Whisper Studio\dictation.json` | dictation settings |
| `C:\Program Files\Whisper Studio\data\models\diarize\` | speaker diarization models |
| `%USERPROFILE%\.cache\huggingface\` | Whisper model cache |

To move data to another computer — copy `%APPDATA%\Whisper Studio\`.

---

## License

MIT — see dependencies (faster-whisper, sherpa-onnx, PySide6) under their own licenses.

---
---

# Whisper Studio (Русский)

Локальная программа для транскрипции аудио на базе **faster-whisper**.
Современный десктоп-интерфейс, всё работает на вашем компьютере: без подписки,
без лимитов, без отправки аудио на чужой сервер.

*Powered by Alazar Studio.*

---

## Установка

1. Скачайте **`WhisperStudio-Setup.exe`** из последнего релиза:
   👉 [github.com/urtenovcom/whisper-studio/releases/latest](https://github.com/urtenovcom/whisper-studio/releases/latest)
2. Запустите установщик — потребуется подтверждение Windows (UAC).
3. Установка занимает 5–10 минут (зависимости качаются из интернета один раз).
4. После завершения программа сама запустится. Ярлык — на рабочем столе и в меню Пуск.

> Поддерживается Windows 10/11 (x64). macOS/Linux пока нет в установщике, но
> код кроссплатформенный — можно запустить вручную (см. ниже).

---

## Возможности

### Транскрипция
- Загрузка аудио/видео перетаскиванием
- Модели на выбор: `small`, `medium`, `large-v3` (для русского — `medium` или `large-v3`)
- Автоматическое использование **GPU NVIDIA**, если он есть (CUDA 12 / cuDNN 9 — ставятся вместе с программой)
- Пакетная обработка нескольких файлов с отменой по кнопке
- Просмотр с таймкодами, перемотка аудио по клику на время
- Редактирование текста (Enter — сохранить, Esc — отменить)
- Закладки на важных репликах
- Поиск по тексту внутри записи
- Экспорт в **TXT, DOCX, SRT, VTT**

### Распознавание говорящих
- Работает «из коробки», **без регистрации на HuggingFace** и без токенов
- Можно указать точное число говорящих (тогда результат заметно лучше)
- Переименование спикеров (Speaker 1 → Имя) применяется ко всем репликам сразу
- Чипсы с найденными говорящими в шапке транскрипта — можно временно скрывать

### Push-to-talk диктовка
- Зажали правый Ctrl (или свою клавишу/комбо) — говорите — отпустили — текст вставится в активное окно
- Работает в любом приложении (мессенджеры, документы, браузер)
- Звуковой сигнал начала записи, плавающая пилюля-эквалайзер поверх всех окон
- Настраивается: клавиша, задержка, модель, язык, микрофон

### Хранение
- **Проекты (папки)** для группировки записей, перемещение между проектами
- Поиск по списку всех транскрипций
- Все данные локально, в `%APPDATA%\Whisper Studio\`

### Интерфейс
- Светлая / тёмная / системная тема
- Русский / английский язык интерфейса
- Сворачивание в трей при закрытии (продолжает работать)
- Авто-запуск при старте Windows (опционально, в Настройках)
- Авто-обновление через GitHub Releases

---

## Запуск вручную (для разработчиков)

Если хотите запустить из исходников или править код:

```bash
# нужен Python 3.12 (под 3.14 пока нет CUDA-wheels у PyTorch для опциональных фич)
python -m venv .venv
.venv\Scripts\activate         # Windows
# source .venv/bin/activate    # macOS/Linux

pip install -r requirements.txt
pip install PySide6 pynput sounddevice pyperclip requests
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12  # только для GPU NVIDIA

python app.py
```

Приложение откроется в собственном окне (Qt WebEngine) и поднимет
локальный сервер на `http://127.0.0.1:8756`.

---

## Где хранятся данные

| Папка | Что внутри |
|---|---|
| `%APPDATA%\Whisper Studio\recordings\` | транскрипции (JSON) |
| `%APPDATA%\Whisper Studio\uploads\` | исходные аудиофайлы |
| `%APPDATA%\Whisper Studio\projects.json` | список проектов |
| `%APPDATA%\Whisper Studio\dictation.json` | настройки диктовки |
| `C:\Program Files\Whisper Studio\data\models\diarize\` | модели определения говорящих |
| `%USERPROFILE%\.cache\huggingface\` | кэш моделей Whisper |

Чтобы перенести данные на другой компьютер — скопируйте папку `%APPDATA%\Whisper Studio\`.

---

## Лицензия

MIT — см. зависимости (faster-whisper, sherpa-onnx, PySide6) под их собственными лицензиями.
