# Speaker Keep-Alive

Keeps your Xiaomi Sound Pocket (or any auto-shutoff Bluetooth speaker) awake by
streaming a continuous silent audio signal in the background.

## Quick Start (run as script)

```
pip install -r requirements.txt
pythonw keepalive.py
```

> Use `pythonw` (not `python`) so no console window appears.

## Build a standalone .exe

Double-click `build.bat` — it installs deps and compiles to `dist\SpeakerKeepAlive.exe`.

## Usage

- Starts silently streaming as soon as it launches
- Tray icon is **green** when active, **gray** when paused
- Right-click the tray icon for options:
  - **Pause / Resume** — toggle the audio stream
  - **Launch on startup** — registers/removes from Windows startup (Registry)
  - **Quit** — stops stream and exits

## Notes

- Uses ~0% CPU, no audible sound
- Works on the currently selected default audio output device
- If you switch audio devices, restart the app
