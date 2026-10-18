# Speaker Keep-Alive

Keeps your Xiaomi Sound Pocket (or any auto-shutoff Bluetooth speaker) awake by
holding a silent "playing" media session on it in the background.

## Quick Start (run as script)

```
pip install -r requirements.txt
pythonw keepalive.py
```

> Use `pythonw` (not `python`) so no console window appears.

## Build a standalone .exe

Double-click `build.bat` — it installs deps and compiles to `dist\SpeakerKeepAlive.exe`.

## Usage

- Starts keeping the speaker awake as soon as it launches
- Tray icon is **green** when active, **gray** when paused
- Right-click the tray icon for options:
  - **Pause / Resume** — toggle the keep-alive
  - **Launch on startup** — registers/removes from Windows startup (Registry)
  - **Quit** — stops the keep-alive and exits

## How it works

The Sound Pocket doesn't listen for sound to decide it's idle. It powers off 15 minutes
after Windows last reported a media session as **Playing** to it over Bluetooth. Tones
at any level or frequency are ignored, even audible ones. So the app loops a silent
clip on the speaker through a Windows media player, which shows up as a playing media
session named "Speaker Keep-Alive" (you'll see it in the volume flyout).

- **Steps aside for real media:** while another app (Spotify, a browser video, ...)
  is playing, the keep-alive pauses; that app's own playing status keeps the speaker
  awake. It resumes when they stop.
- **Media keys still control your music:** Windows sometimes sends play/pause/next
  (keyboard keys or the speaker's own button) to the keep-alive session. Those are
  passed on to the app that played last.
- **Only the speaker:** it plays to the speaker named by `SPEAKER_NAME` in `audio.py`
  (default `"Sound Pocket"`), whatever the Windows default output is, so the speaker
  stays awake while you use headphones. Nothing runs while the speaker is off; the
  session comes back when it reconnects (checked every 2 s). For a different speaker,
  set `SPEAKER_NAME` to part of its name as shown in Windows Sound settings
- Uses ~0% CPU, no audible sound
