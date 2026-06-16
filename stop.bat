@echo off
echo Stopping all servers...
taskkill /FI "WINDOWTITLE eq Backend API*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Frontend Dev Server*" /T /F >nul 2>&1
echo Done.
pause
