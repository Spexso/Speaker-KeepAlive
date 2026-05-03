import os
import sys
import tempfile
import subprocess
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw

import audio
import systemreg

APP_NAME = "SpeakerKeepAlive"


def create_icon(active=True):
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    color = (34, 197, 94) if active else (107, 114, 128)
    draw.ellipse([4, 4, 60, 60], fill=color)

    draw.rectangle([18, 24, 28, 40], fill="white")
    draw.polygon([(28, 20), (42, 14), (42, 50), (28, 44)], fill="white")

    if active:
        draw.arc([44, 22, 54, 42], start=-60, end=60, fill="white", width=3)
        draw.arc([47, 26, 57, 38], start=-60, end=60, fill="white", width=2)

    return img


def get_status_label():
    return "● Active, keeping speaker alive" if audio.is_playing else "○ Paused"


def get_toggle_label():
    return "Pause" if audio.is_playing else "Resume"


def build_menu(icon):
    return pystray.Menu(
        item(get_status_label(), lambda i, it: None, enabled=False),
        pystray.Menu.SEPARATOR,
        item(get_toggle_label(), lambda i, it: on_toggle(icon)),
        item("Launch on startup", lambda i, it: on_toggle_startup(icon),
             checked=lambda i: systemreg.is_startup_enabled()),
        pystray.Menu.SEPARATOR,
        item("Quit", lambda i, it: on_quit(icon)),
        pystray.Menu.SEPARATOR,
        item("Uninstall", lambda i, it: on_uninstall(icon)),
    )


def on_toggle(icon):
    if audio.is_playing:
        audio.stop_audio()
    else:
        audio.start_audio()
    icon.icon = create_icon(audio.is_playing)
    icon.menu = build_menu(icon)


def on_toggle_startup(icon):
    systemreg.toggle_startup()
    icon.menu = build_menu(icon)


def on_quit(icon):
    audio.stop_audio()
    icon.stop()


def on_uninstall(icon):
    systemreg.disable_startup()
    audio.stop_audio()

    if getattr(sys, 'frozen', False):
        exe_path = sys.executable
        bat = (
            "@echo off\n"
            "timeout /t 2 /nobreak >nul\n"
            f'del /f "{exe_path}"\n'
            "del /f \"%~f0\"\n"
        )
        fd, bat_path = tempfile.mkstemp(suffix=".bat")
        with os.fdopen(fd, "w") as f:
            f.write(bat)
        subprocess.Popen(
            ["cmd", "/c", bat_path],
            creationflags=subprocess.CREATE_NO_WINDOW,
            close_fds=True,
        )

    icon.stop()


def run():
    audio.start_audio()

    icon = pystray.Icon(
        APP_NAME,
        create_icon(True),
        "Speaker Keep-Alive",
    )
    icon.menu = build_menu(icon)
    icon.run()
