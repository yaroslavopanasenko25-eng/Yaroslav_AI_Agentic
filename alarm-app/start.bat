@echo off
echo Starting Ukraine Alarm Shield...
echo.

:: Start Python backend (all API routes + Python UI)
echo [1/2] Starting Python backend on 0.0.0.0:8080...
cd ..\backend
start "Python Backend" cmd /c "pip install -r requirements.txt -q && python run_server.py"
cd ..\alarm-app

timeout /t 3 /nobreak >nul

:: Start frontend (legacy React — optional)
echo [2/2] Starting frontend on 0.0.0.0:5173...
cd frontend
start "Frontend" cmd /c "npm install && npm run dev -- --host 0.0.0.0"
cd ..

echo.
echo  Python UI (recommended): http://127.0.0.1:8080
echo  React UI (legacy):       http://127.0.0.1:5173
echo.
echo  Other devices on Wi-Fi: use http://YOUR_PC_IP:8080 (see ipconfig)
echo.
pause
