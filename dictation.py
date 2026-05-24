"""Push-to-talk dictation: hotkey -> record -> transcribe -> paste."""

import json
import sys
import threading
import time
from pathlib import Path
from typing import Optional

import numpy as np

try:
    import sounddevice as sd
    import pyperclip
    from pynput import keyboard
    _HAS_DEPS = True
except Exception:
    _HAS_DEPS = False

try:
    import overlay as _overlay_mod
except Exception:
    _overlay_mod = None


def _overlay_safe(method, *args, **kwargs):
    if _overlay_mod is None:
        return
    try:
        ov = _overlay_mod.get_overlay()
        getattr(ov, method)(*args, **kwargs)
    except Exception:
        pass

SAMPLE_RATE = 16000

_BASE = Path(__file__).parent.resolve()
_SOUND_ON = _BASE / "resources" / "dict_on.wav"
_SOUND_OFF = _BASE / "resources" / "dict_off.wav"


def _play_sound(path):
    """Короткий звук, асинхронно (Windows). Не блокирует."""
    if sys.platform != "win32" or not path.exists():
        return
    try:
        import winsound
        winsound.PlaySound(
            str(path),
            winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT,
        )
    except Exception:
        pass


def _send_paste():
    """Отправить Ctrl+V в активное окно. На Windows — через keybd_event."""
    if sys.platform == "win32":
        import ctypes
        VK_CONTROL = 0x11
        VK_V = 0x56
        KEYUP = 0x0002
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        # Подождём, чтобы пользовательские клавиши успели отпуститься
        time.sleep(0.05)
        user32.keybd_event(VK_CONTROL, 0, 0, 0)
        time.sleep(0.01)
        user32.keybd_event(VK_V, 0, 0, 0)
        time.sleep(0.02)
        user32.keybd_event(VK_V, 0, KEYUP, 0)
        time.sleep(0.01)
        user32.keybd_event(VK_CONTROL, 0, KEYUP, 0)
    else:
        ctrl = keyboard.Controller()
        time.sleep(0.05)
        with ctrl.pressed(keyboard.Key.ctrl):
            ctrl.press("v")
            ctrl.release("v")


class DictationState:
    IDLE = "idle"
    LISTENING = "listening"
    RECORDING = "recording"
    TRANSCRIBING = "transcribing"


DEFAULT_SETTINGS = {
    "enabled": False,
    "hotkey": ["ctrl_r"],
    "hold_ms": 1000,
    "model": "small",
    "language": "ru",
    "device_index": None,
}


_state = {
    "settings": dict(DEFAULT_SETTINGS),
    "settings_path": None,
    "model_loader": None,
    "listener": None,
    "status": DictationState.IDLE,
    "pressed_keys": set(),
    "hold_timer": None,
    "recording_thread": None,
    "audio_buffer": [],
    "stop_recording": threading.Event(),
    "model_cache": {},
}
_lock = threading.Lock()


def _key_to_name(key) -> Optional[str]:
    if not _HAS_DEPS:
        return None
    from pynput.keyboard import Key, KeyCode
    if isinstance(key, Key):
        return key.name
    if isinstance(key, KeyCode):
        if key.char:
            return key.char.lower()
        return None
    return None


def _normalize_mod(name: str) -> str:
    if name in ("ctrl_l", "ctrl_r"):
        return "ctrl"
    if name in ("alt_l", "alt_r", "alt_gr"):
        return "alt"
    if name in ("shift_l", "shift_r"):
        return "shift"
    if name in ("cmd_l", "cmd_r", "cmd"):
        return "cmd"
    return name


def init(settings_path: Path, model_loader):
    _state["settings_path"] = settings_path
    _state["model_loader"] = model_loader
    _load_settings()
    if _state["settings"].get("enabled"):
        start_listener()


def _load_settings():
    p = _state["settings_path"]
    if p and p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            _state["settings"] = {**DEFAULT_SETTINGS, **data}
            return
        except Exception:
            pass
    _state["settings"] = dict(DEFAULT_SETTINGS)


def save_settings(new_settings: dict):
    merged = {**_state["settings"], **(new_settings or {})}
    _state["settings"] = merged
    p = _state["settings_path"]
    if p:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    stop_listener()
    if merged.get("enabled"):
        start_listener()
    return merged


def start_listener():
    if not _HAS_DEPS:
        return False
    if _state["listener"] is not None:
        return True
    _state["pressed_keys"] = set()
    listener = keyboard.Listener(on_press=_on_press, on_release=_on_release)
    listener.daemon = True
    listener.start()
    _state["listener"] = listener
    threading.Thread(target=_preload_model, daemon=True).start()
    return True


def _preload_model():
    try:
        size = _state["settings"]["model"]
        if size not in _state["model_cache"]:
            _state["model_cache"][size] = _state["model_loader"](size)
    except Exception as e:
        print(f"[dictation] preload error: {e}")


def stop_listener():
    if _state["listener"]:
        try:
            _state["listener"].stop()
        except Exception:
            pass
        _state["listener"] = None
    _state["stop_recording"].set()
    _state["pressed_keys"] = set()
    if _state["hold_timer"]:
        try:
            _state["hold_timer"].cancel()
        except Exception:
            pass
        _state["hold_timer"] = None
    _state["status"] = DictationState.IDLE


def _on_press(key):
    name = _key_to_name(key)
    if not name:
        return
    _state["pressed_keys"].add(name)
    _check_hotkey_match()


def _on_release(key):
    name = _key_to_name(key)
    if not name:
        return
    _state["pressed_keys"].discard(name)
    _check_release()


def _hotkey_matches() -> bool:
    hk = _state["settings"].get("hotkey") or []
    if not hk:
        return False
    if len(hk) == 1:
        return hk[0] in _state["pressed_keys"]
    pressed_norm = {_normalize_mod(k) for k in _state["pressed_keys"]}
    needed_norm = {_normalize_mod(k) for k in hk}
    return needed_norm.issubset(pressed_norm)


def _check_hotkey_match():
    if _state["status"] != DictationState.IDLE:
        return
    if not _hotkey_matches():
        return
    s = _state["settings"]
    hk = s.get("hotkey") or []
    print(f"[dictation] hotkey matched: {hk} (pressed={sorted(_state['pressed_keys'])})", flush=True)
    if len(hk) == 1:
        _state["status"] = DictationState.LISTENING
        hold_ms = max(0, int(s.get("hold_ms") or 0))
        if hold_ms <= 0:
            _start_recording()
            return
        t = threading.Timer(hold_ms / 1000.0, _maybe_start_recording)
        t.daemon = True
        t.start()
        _state["hold_timer"] = t
    else:
        _start_recording()


def _maybe_start_recording():
    if _state["status"] == DictationState.LISTENING and _hotkey_matches():
        _start_recording()
    else:
        _state["status"] = DictationState.IDLE


def _check_release():
    if _state["status"] == DictationState.LISTENING:
        if _state["hold_timer"]:
            try:
                _state["hold_timer"].cancel()
            except Exception:
                pass
            _state["hold_timer"] = None
        _state["status"] = DictationState.IDLE
        return
    if _state["status"] == DictationState.RECORDING:
        if not _hotkey_matches():
            _stop_and_transcribe()


def _start_recording():
    if _state["status"] == DictationState.RECORDING:
        return
    print(f"[dictation] start recording (mic={_state['settings'].get('device_index')})", flush=True)
    _state["status"] = DictationState.RECORDING
    _state["audio_buffer"] = []
    _state["stop_recording"] = threading.Event()
    _play_sound(_SOUND_ON)
    _overlay_safe("show", "recording")
    t = threading.Thread(target=_record_loop, daemon=True)
    _state["recording_thread"] = t
    t.start()


def _record_loop():
    device = _state["settings"].get("device_index")
    try:
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            device=device,
            blocksize=1600,
            callback=_audio_callback,
        ):
            while not _state["stop_recording"].is_set():
                _state["stop_recording"].wait(timeout=0.05)
    except Exception as e:
        print(f"[dictation] record error: {e}")
        _state["status"] = DictationState.IDLE


def _audio_callback(indata, frames, time_info, status):
    _state["audio_buffer"].append(indata.copy())
    _overlay_safe("update_level", indata[:, 0])


def _stop_and_transcribe():
    _state["stop_recording"].set()
    _state["status"] = DictationState.TRANSCRIBING
    _overlay_safe("set_mode", "transcribing")
    t = threading.Thread(target=_do_transcribe, daemon=True)
    t.start()


def _do_transcribe():
    try:
        rec_t = _state["recording_thread"]
        if rec_t:
            rec_t.join(timeout=2.0)
        buf = _state["audio_buffer"]
        print(f"[dictation] transcribing… buffer chunks={len(buf)}", flush=True)
        if not buf:
            return
        audio = np.concatenate(buf).flatten()
        secs = len(audio) / SAMPLE_RATE
        print(f"[dictation] audio length={secs:.2f}s max_amp={float(np.abs(audio).max() if len(audio) else 0):.4f}", flush=True)
        if len(audio) < SAMPLE_RATE * 0.3:
            print("[dictation] too short, skipping", flush=True)
            return
        s = _state["settings"]
        size = s["model"]
        model = _state["model_cache"].get(size)
        if model is None:
            model = _state["model_loader"](size)
            _state["model_cache"][size] = model
        lang = s.get("language") or None
        if lang == "auto":
            lang = None
        segments_gen, _info = model.transcribe(
            audio, language=lang, beam_size=5, vad_filter=True
        )
        text = " ".join(seg.text.strip() for seg in segments_gen).strip()
        print(f"[dictation] text: {text!r}", flush=True)
        if not text:
            return
        pyperclip.copy(text + " ")
        _send_paste()
    except Exception as e:
        print(f"[dictation] transcribe error: {e}")
    finally:
        _state["status"] = DictationState.IDLE
        _overlay_safe("hide")


def get_status():
    s = _state["settings"]
    return {
        "available": _HAS_DEPS,
        "running": _state["listener"] is not None,
        "status": _state["status"],
        "settings": s,
    }


def list_microphones():
    if not _HAS_DEPS:
        return []
    try:
        devs = sd.query_devices()
        out = []
        for i, d in enumerate(devs):
            if d.get("max_input_channels", 0) > 0:
                out.append({"index": i, "name": d["name"]})
        return out
    except Exception:
        return []
