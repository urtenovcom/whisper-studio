"""Главное окно (Qt WebEngine) + системная трей-иконка."""

import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QUrl, QStandardPaths
from PySide6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor, QPen
from PySide6.QtWidgets import (
    QMainWindow, QSystemTrayIcon, QMenu, QApplication,
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEngineDownloadRequest


def make_app_icon(size: int = 64) -> QIcon:
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    # фиолетовый закруглённый квадрат
    p.setBrush(QColor(99, 102, 241))
    p.setPen(Qt.NoPen)
    r = size * 0.22
    p.drawRoundedRect(0, 0, size, size, r, r)
    # микрофон
    p.setBrush(QColor(255, 255, 255))
    mic_w = size * 0.25
    mic_h = size * 0.40
    mic_x = (size - mic_w) / 2
    mic_y = size * 0.18
    p.drawRoundedRect(mic_x, mic_y, mic_w, mic_h, mic_w / 2, mic_w / 2)
    # подкова и ножка
    pen = QPen(QColor(255, 255, 255), max(2, size * 0.05),
               Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    arc_x = size * 0.28
    arc_y = size * 0.36
    arc_w = size * 0.44
    arc_h = size * 0.35
    p.drawArc(arc_x, arc_y, arc_w, arc_h, 200 * 16, 140 * 16)
    p.drawLine(size / 2, size * 0.72, size / 2, size * 0.84)
    p.end()
    return QIcon(pix)


class MainWindow(QMainWindow):
    def __init__(self, url: str, tray_ref=None):
        super().__init__()
        self.setWindowTitle("Whisper Studio")
        self.resize(1280, 720)
        self.setMinimumSize(1280, 720)
        self.setWindowIcon(make_app_icon(64))
        self.web = QWebEngineView(self)
        # Подключаем обработчик загрузок — экспорт файлов уходит в Загрузки
        profile = self.web.page().profile()
        profile.downloadRequested.connect(self._on_download_requested)
        self.web.load(QUrl(url))
        self.setCentralWidget(self.web)
        self._force_quit = False
        self._tray_ref = tray_ref

    def _on_download_requested(self, download: QWebEngineDownloadRequest):
        from PySide6.QtWidgets import QFileDialog
        downloads_dir = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
        if not downloads_dir:
            downloads_dir = str(Path.home() / "Downloads")
        name = download.suggestedFileName() or "whisper-export"
        default_path = str(Path(downloads_dir) / name)
        # Подсказываем фильтр по расширению
        ext = Path(name).suffix.lower().lstrip(".")
        filt = "Все файлы (*.*)"
        if ext:
            filt = f"Файл *.{ext} (*.{ext});;Все файлы (*.*)"
        target, _ = QFileDialog.getSaveFileName(
            self, "Сохранить как", default_path, filt
        )
        if not target:
            download.cancel()
            return
        target_path = Path(target)
        download.setDownloadDirectory(str(target_path.parent))
        download.setDownloadFileName(target_path.name)
        download.accept()
        def _finished():
            if download.state() == QWebEngineDownloadRequest.DownloadCompleted:
                try:
                    if sys.platform == "win32":
                        subprocess.Popen(["explorer", "/select,", str(target_path)])
                except Exception:
                    pass
        download.isFinishedChanged.connect(_finished)

    def closeEvent(self, event):
        if self._force_quit:
            event.accept()
        else:
            event.ignore()
            self.hide()

    def request_quit(self):
        self._force_quit = True
        self.close()


def apply_app_icon(app: QApplication):
    """Применяет иконку на уровне всего приложения + регистрирует AppUserModelID,
    чтобы Windows не показывал стандартный значок Python в панели задач."""
    icon = make_app_icon(256)
    app.setWindowIcon(icon)
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "WhisperStudio.WhisperStudio.1.0"
            )
        except Exception as e:
            print(f"[main] AppUserModelID set failed: {e}", flush=True)


def setup_tray(app: QApplication, window: MainWindow) -> QSystemTrayIcon:
    icon = make_app_icon(64)
    tray = QSystemTrayIcon(icon, app)
    tray.setToolTip("Whisper Studio")

    menu = QMenu()
    act_show = QAction("Открыть", menu)
    act_show.triggered.connect(lambda: (window.showNormal(), window.raise_(), window.activateWindow()))
    menu.addAction(act_show)
    menu.addSeparator()
    act_quit = QAction("Выход", menu)
    act_quit.triggered.connect(lambda: _quit(app, window))
    menu.addAction(act_quit)

    tray.setContextMenu(menu)
    # Реагируем только на правый клик (контекстное меню) — обычный клик игнорируем
    tray.show()
    window._tray_ref = tray
    return tray


def _quit(app: QApplication, window: MainWindow):
    window._force_quit = True
    app.quit()
