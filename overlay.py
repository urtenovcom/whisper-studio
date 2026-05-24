"""iOS-подобный плавающий оверлей с эквалайзером на PySide6 (Qt)."""

import math
import sys
import threading
from typing import Optional

import numpy as np

try:
    from PySide6.QtCore import Qt, QTimer, QObject, Signal
    from PySide6.QtGui import (
        QPainter, QColor, QPainterPath, QBrush, QPen, QLinearGradient,
    )
    from PySide6.QtWidgets import QApplication, QWidget
    _HAS_QT = True
except Exception as _e:
    _HAS_QT = False
    print(f"[overlay] PySide6 not available: {_e}", flush=True)


NUM_BARS = 5
BAR_WIDTH = 4
BAR_GAP = 12
PILL_PADDING_H = 22
PILL_HEIGHT = 44
SHADOW_PAD = 10
BOTTOM_OFFSET = 50


if _HAS_QT:

    class OverlayWindow(QWidget):
        sig_level = Signal(object)
        sig_show = Signal(str)
        sig_hide = Signal()
        sig_mode = Signal(str)

        def __init__(self):
            super().__init__()
            self.setWindowFlags(
                Qt.FramelessWindowHint
                | Qt.WindowStaysOnTopHint
                | Qt.Tool
                | Qt.WindowDoesNotAcceptFocus
            )
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setAttribute(Qt.WA_ShowWithoutActivating)

            self.pill_w = (
                NUM_BARS * BAR_WIDTH
                + (NUM_BARS - 1) * BAR_GAP
                + PILL_PADDING_H * 2
            )
            self.pill_h = PILL_HEIGHT
            self.total_w = self.pill_w + SHADOW_PAD * 2
            self.total_h = self.pill_h + SHADOW_PAD * 2
            self.resize(self.total_w, self.total_h)

            screen = QApplication.primaryScreen().availableGeometry()
            x = (screen.width() - self.total_w) // 2
            y = screen.height() - self.total_h - BOTTOM_OFFSET
            self.move(x, y)

            self.targets = [0.0] * NUM_BARS
            self.currents = [0.0] * NUM_BARS
            self.mode = "idle"
            self.t = 0.0
            self._click_through_applied = False

            self.timer = QTimer(self)
            self.timer.timeout.connect(self._animate)
            self.timer.start(16)  # ~60 FPS

            self.sig_level.connect(self._on_level)
            self.sig_show.connect(self._on_show)
            self.sig_hide.connect(self._on_hide)
            self.sig_mode.connect(self._on_mode)

        def _animate(self):
            for i in range(NUM_BARS):
                self.currents[i] += (self.targets[i] - self.currents[i]) * 0.32
            self.t += 0.16
            if self.isVisible():
                self.update()

        def _on_level(self, arr):
            try:
                a = np.asarray(arr, dtype=np.float32).flatten()
                if not a.size:
                    return
                rms = float(np.sqrt(np.mean(a * a)))
                # peak обычно даёт более «живые» столбики
                peak = float(np.max(np.abs(a))) if a.size else 0.0
                lvl = max(rms * 18.0, peak * 4.0)
                base = min(1.0, lvl)
                pattern = [0.55, 0.85, 1.0, 0.85, 0.55]
                self.targets = [
                    min(1.0, base * pattern[i]) for i in range(NUM_BARS)
                ]
            except Exception:
                pass

        def _on_show(self, mode):
            self.mode = mode
            self.targets = [0.0] * NUM_BARS
            self.currents = [0.0] * NUM_BARS
            self.show()
            self.raise_()
            if not self._click_through_applied:
                self._apply_click_through()
                self._click_through_applied = True

        def _on_hide(self):
            self.hide()

        def _on_mode(self, mode):
            self.mode = mode

        def _apply_click_through(self):
            if sys.platform != "win32":
                return
            try:
                import ctypes
                hwnd = int(self.winId())
                user32 = ctypes.windll.user32
                GWL_EXSTYLE = -20
                WS_EX_LAYERED = 0x00080000
                WS_EX_TRANSPARENT = 0x00000020
                WS_EX_NOACTIVATE = 0x08000000
                WS_EX_TOOLWINDOW = 0x00000080
                style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                user32.SetWindowLongW(
                    hwnd, GWL_EXSTYLE,
                    style
                    | WS_EX_LAYERED
                    | WS_EX_TRANSPARENT
                    | WS_EX_NOACTIVATE
                    | WS_EX_TOOLWINDOW,
                )
            except Exception as e:
                print(f"[overlay] click-through failed: {e}", flush=True)

        def paintEvent(self, event):
            p = QPainter(self)
            p.setRenderHint(QPainter.Antialiasing, True)
            p.setRenderHint(QPainter.SmoothPixmapTransform, True)

            sp = SHADOW_PAD
            px, py = sp, sp
            pw, ph = self.pill_w, self.pill_h
            radius = ph / 2

            # Лёгкая тень под капсулой
            for i in range(4, 0, -1):
                alpha = int(24 * (1 - i / 5.0))
                if alpha <= 0:
                    continue
                sd_path = QPainterPath()
                sd_path.addRoundedRect(
                    px - i * 0.7,
                    py + 2,
                    pw + i * 1.4,
                    ph + i * 0.7,
                    radius + i * 0.7,
                    radius + i * 0.7,
                )
                p.fillPath(sd_path, QColor(0, 0, 0, alpha))

            # Капсула — тёмный градиент сверху вниз
            pill_path = QPainterPath()
            pill_path.addRoundedRect(px, py, pw, ph, radius, radius)
            grad = QLinearGradient(0, py, 0, py + ph)
            grad.setColorAt(0.0, QColor(34, 36, 48, 240))
            grad.setColorAt(1.0, QColor(16, 18, 26, 240))
            p.fillPath(pill_path, QBrush(grad))

            # Лёгкий внутренний хайлайт сверху
            hl_pen = QPen(QColor(255, 255, 255, 28))
            hl_pen.setWidthF(1.0)
            p.setPen(hl_pen)
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(
                px + 0.5, py + 0.5, pw - 1, ph - 1,
                radius - 0.5, radius - 0.5,
            )

            # Столбики
            total_bar_w = NUM_BARS * BAR_WIDTH + (NUM_BARS - 1) * BAR_GAP
            bar_x0 = px + (pw - total_bar_w) / 2
            cy = py + ph / 2
            max_bar_h = ph - 12

            if self.mode == "transcribing":
                color = QColor(252, 211, 77)
                for i in range(NUM_BARS):
                    amp = 0.22 + 0.22 * abs(math.sin(self.t * 0.6 + i * 0.7))
                    self._draw_bar(
                        p, bar_x0 + i * (BAR_WIDTH + BAR_GAP),
                        cy, amp * max_bar_h, color,
                    )
            else:
                color = QColor(245, 245, 247)
                for i, lv in enumerate(self.currents):
                    idle = 0.12 + 0.05 * math.sin(self.t * 0.5 + i * 0.9)
                    h = max(idle, lv) * max_bar_h
                    self._draw_bar(
                        p, bar_x0 + i * (BAR_WIDTH + BAR_GAP),
                        cy, h, color,
                    )

            p.end()

        def _draw_bar(self, p, x, cy, h, color):
            h = max(3.0, h)
            path = QPainterPath()
            path.addRoundedRect(
                x, cy - h / 2.0, BAR_WIDTH, h, BAR_WIDTH / 2.0, BAR_WIDTH / 2.0,
            )
            p.fillPath(path, color)


    class OverlayController(QObject):
        def __init__(self):
            super().__init__()
            self.window: Optional[OverlayWindow] = None

        def ensure_window(self):
            if self.window is None:
                self.window = OverlayWindow()
            return self.window

        def show(self, mode="recording"):
            w = self.ensure_window()
            w.sig_show.emit(mode)

        def hide(self):
            if self.window:
                self.window.sig_hide.emit()

        def update_level(self, audio_chunk):
            if self.window and self.window.isVisible():
                self.window.sig_level.emit(audio_chunk)

        def set_mode(self, mode):
            if self.window:
                self.window.sig_mode.emit(mode)

else:
    class OverlayController:
        def show(self, mode="recording"): pass
        def hide(self): pass
        def update_level(self, audio_chunk): pass
        def set_mode(self, mode): pass
        def ensure_window(self): pass


_overlay: Optional["OverlayController"] = None
_overlay_lock = threading.Lock()


def init_on_main_thread():
    """Должен вызываться один раз на основном потоке до старта uvicorn."""
    global _overlay
    if not _HAS_QT:
        return None
    with _overlay_lock:
        if _overlay is None:
            _overlay = OverlayController()
            _overlay.ensure_window()  # создаём окно сразу на главном потоке
    return _overlay


def get_overlay():
    global _overlay
    with _overlay_lock:
        if _overlay is None:
            _overlay = OverlayController()
        return _overlay


def has_qt():
    return _HAS_QT
