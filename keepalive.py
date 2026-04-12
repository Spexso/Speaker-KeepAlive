import sys
import os
import threading
import time
import winreg
import numpy as np
import sounddevice as sd
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as item

APP_NAME = "SpeakerKeepAlive"
SAMPLE_RATE = 44100
BLOCK_SIZE = 1024

# --- Audio ---

stream = None
stream_lock = threading.Lock()
is_playing = False

def audio_callback(outdata, frames, time_info, status):
    outdata[:] = np.zeros((frames, 1), dtype=np.float32)

def start_audio():
    global stream, is_playing
    with stream_lock:
        if stream is not None:
            return
        stream = sd.OutputStream(
            samplerate=SAMPLE_RATE,
            blocksize=BLOCK_SIZE,
            channels=1,
            dtype='float32',
            callback=audio_callback
        )
        stream.start()
        is_playing = True

def stop_audio():
    global stream, is_playing
    with stream_lock:
        if stream is None:
            return
        stream.stop()
        stream.close()
        stream = None
        is_playing = False

# --- Tray Icon ---

def create_icon(active=True):
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Circle background
    color = (34, 197, 94) if active else (107, 114, 128)  # green or gray
    draw.ellipse([4, 4, 60, 60], fill=color)

    # Speaker shape (simple)
    # Body
    draw.rectangle([18, 24, 28, 40], fill="white")
    # Cone
    draw.polygon([(28, 20), (42, 14), (42, 50), (28, 44)], fill="white")
    # Sound waves if active
    if active:
        draw.arc([44, 22, 54, 42], start=-60, end=60, fill="white", width=3)
        draw.arc([47, 26, 57, 38], start=-60, end=60, fill="white", width=2)

    return img

def on_toggle(icon, item_ref):
    global is_playing
    if is_playing:
        stop_audio()
    else:
        start_audio()
    icon.icon = create_icon(is_playing)
    icon.menu = build_menu(icon)

def on_quit(icon, item_ref):
    stop_audio()
    icon.stop()

def get_status_label():
    return "Active, keeping speaker alive" if is_playing else "Paused"

def get_toggle_label():
    return "Pause" if is_playing else "Resume"

def build_menu(icon):
    return pystray.Menu(
        item(get_status_label(), lambda i, it: None, enabled=False),
        pystray.Menu.SEPARATOR,
        item(get_toggle_label(), on_toggle),
        item("Launch on startup", on_toggle_startup, checked=lambda i: is_startup_enabled()),
        pystray.Menu.SEPARATOR,
        item("Quit", on_quit),
    )

# --- Startup ---

def get_exe_path():
    if getattr(sys, 'frozen', False):
        return sys.executable
    return f'pythonw "{os.path.abspath(__file__)}"'

def is_startup_enabled():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, winreg.KEY_READ)
        winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False

def enable_startup():
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                         r"Software\Microsoft\Windows\CurrentVersion\Run",
                         0, winreg.KEY_SET_VALUE)
    winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, get_exe_path())
    winreg.CloseKey(key)

def disable_startup():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, APP_NAME)
        winreg.CloseKey(key)
    except FileNotFoundError:
        pass

def on_toggle_startup(icon, item_ref):
    if is_startup_enabled():
        disable_startup()
    else:
        enable_startup()
    icon.menu = build_menu(icon)

# --- Main ---

def main():
    start_audio()

    icon = pystray.Icon(
        APP_NAME,
        create_icon(True),
        "Speaker Keep-Alive",
    )
    icon.menu = build_menu(icon)
    icon.run()

if __name__ == "__main__":
    main()
