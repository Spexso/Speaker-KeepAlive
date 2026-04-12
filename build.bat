@echo off
echo Installing dependencies...
pip install sounddevice numpy pillow pystray pyinstaller

echo.
echo Building executable...
pyinstaller --onefile --windowed --name SpeakerKeepAlive keepalive.py

echo.
echo Done! Executable is in dist\SpeakerKeepAlive.exe
echo Run it once, then enable "Launch on startup" from the tray icon.
pause
