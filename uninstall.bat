@echo off
echo Uninstalling Speaker Keep-Alive...
echo.

echo Stopping running instance...
taskkill /f /im SpeakerKeepAlive.exe 2>nul
if %errorlevel%==0 (
    echo   Stopped.
) else (
    echo   Not running.
)

echo Removing startup registry entry...
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "SpeakerKeepAlive" /f 2>nul
if %errorlevel%==0 (
    echo   Registry entry removed.
) else (
    echo   No registry entry found.
)

echo Deleting executable...
if exist "%~dp0dist\SpeakerKeepAlive.exe" (
    del /f "%~dp0dist\SpeakerKeepAlive.exe"
    echo   dist\SpeakerKeepAlive.exe deleted.
) else (
    echo   dist\SpeakerKeepAlive.exe not found.
)

echo.
echo Speaker Keep-Alive has been uninstalled.
pause
