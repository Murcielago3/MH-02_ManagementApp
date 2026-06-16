@echo off
cd /d "%~dp0"

:: Detect LAN IP - prefer 192.168.x.x then 10.x.x.x, skip Docker/WSL 172.x.x.x
for /f %%i in ('powershell -NoProfile -Command "$ip = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -like '192.168.*' } | Select-Object -First 1 -ExpandProperty IPAddress; if (-not $ip) { $ip = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -like '10.*' } | Select-Object -First 1 -ExpandProperty IPAddress }; $ip"') do set LOCAL_IP=%%i

if "%LOCAL_IP%"=="" (
    echo ERROR: Could not detect LAN IP. Check your network connection.
    pause
    exit /b 1
)

echo Local IP: %LOCAL_IP%

:: Write frontend env with correct API URL
echo VITE_API_URL=http://%LOCAL_IP%:8000> frontend\.env

:: Start backend in its own window
start "Backend API" cmd /k "cd /d "%~dp0backend" && "%~dp0.venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

:: Start frontend in its own window
start "Frontend Dev Server" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo ============================================
echo   Frontend : http://%LOCAL_IP%:5173
echo   Backend  : http://%LOCAL_IP%:8000
echo ============================================
echo.
pause
