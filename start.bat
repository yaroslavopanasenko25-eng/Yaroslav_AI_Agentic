@echo off
setlocal enabledelayedexpansion

echo Starting GuardianEye (Python UI + API)...
echo.

cd /d "%~dp0backend"

echo Installing dependencies...
pip install -r requirements.txt -q

echo.
echo Starting server on 0.0.0.0:8080 (accessible from other devices on Wi-Fi)...
echo.

for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
  set "IP=%%a"
  set "IP=!IP:~1!"
  goto :found_ip
)
:found_ip

start "GuardianEye" cmd /k "python run_server.py"

timeout /t 2 /nobreak >nul

echo  On this PC:  http://127.0.0.1:8080
if defined IP echo  On Wi-Fi:    http://!IP!:8080
echo.
echo  API docs:   http://127.0.0.1:8080/docs
echo  API index:  http://127.0.0.1:8080/api/v1
echo.
echo  Works in demo mode without API keys after git clone.
echo  Edit backend/.env for live alerts.in.ua + Grok AI.
echo.
pause
