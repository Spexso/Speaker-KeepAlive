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
- Plays to the Windows default audio output device, and automatically follows it
  when the default changes or the speaker disconnects/reconnects (checked every 3 s)
- The keep-alive signal is a 19 kHz tone at -30 dBFS: above adult hearing, but inside
  the speaker's frequency range so it isn't treated as silence. Sub-bass tones don't
  work: small speakers filter them out (the Sound Pocket's range starts at 100 Hz)
  and still power off after their idle timeout (15 min). If your speaker still shuts
  off, raise `TONE_AMPLITUDE` in `audio.py`; if you can hear a faint whine, raise
  `TONE_HZ` toward 20000 or reduce `TONE_AMPLITUDE`
