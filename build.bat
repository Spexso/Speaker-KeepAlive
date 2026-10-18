@echo off
echo Installing dependencies...
pip install -r requirements.txt pyinstaller

echo.
echo Building executable...
pyinstaller --onefile --windowed --name SpeakerKeepAlive keepalive.py

echo.
echo Done! Executable is in dist\SpeakerKeepAlive.exe
echo Run it once, then enable "Launch on startup" from the tray icon.
pause
