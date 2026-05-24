"""Генерирует app.ico с несколькими разрешениями из нашей make_app_icon()."""
import io
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import QBuffer, QByteArray, QIODevice
from PySide6.QtWidgets import QApplication

# Чтобы импорт mainwindow прошёл, нам нужно QApplication
app = QApplication.instance() or QApplication([])

from mainwindow import make_app_icon

SIZES = [16, 24, 32, 48, 64, 128, 256]

def png_bytes_for(size: int) -> bytes:
    icon = make_app_icon(size)
    pix = icon.pixmap(size, size)
    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QIODevice.WriteOnly)
    pix.save(buf, "PNG")
    return bytes(ba)

def build_ico(out_path: Path):
    images = [(s, png_bytes_for(s)) for s in SIZES]
    # ICONDIR header
    header = struct.pack("<HHH", 0, 1, len(images))  # reserved, type=1 (ico), count
    # ICONDIRENTRY structs
    offset = 6 + 16 * len(images)
    entries = b""
    blobs = b""
    for size, png in images:
        w = 0 if size >= 256 else size
        h = 0 if size >= 256 else size
        entries += struct.pack(
            "<BBBBHHII",
            w, h, 0, 0,    # width, height, colors, reserved
            1, 32,         # planes, bits per pixel
            len(png), offset,
        )
        blobs += png
        offset += len(png)
    out_path.write_bytes(header + entries + blobs)
    print(f"wrote {out_path} ({out_path.stat().st_size} bytes)")

if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("installer/app.ico")
    out.parent.mkdir(parents=True, exist_ok=True)
    build_ico(out)
