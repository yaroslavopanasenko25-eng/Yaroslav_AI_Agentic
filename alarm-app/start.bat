@echo off
echo Starting Ukraine Alarm Shield...
echo.

:: Start Python backend (all API routes)
echo [1/2] Starting Python backend on port 8080...
cd ..\backend
start "Python Backend" cmd /c "pip install -r requirements.txt -q && uvicorn main:app --host 127.0.0.1 --port 8080 --reload"
cd ..\alarm-app

timeout /t 3 /nobreak >nul

:: Start frontend
echo [2/2] Starting frontend on port 5173...
cd frontend
start "Frontend" cmd /c "npm install && npm run dev"
cd ..

echo.
echo  Python API: http://localhost:8080
echo  Frontend:   http://localhost:5173
echo.
pause
