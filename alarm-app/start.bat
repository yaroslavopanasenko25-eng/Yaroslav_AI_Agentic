@echo off
echo Starting Ukraine Alarm Shield...
echo.

:: Start Python backend (Grok AI + alerts API)
echo [1/3] Starting Python backend on port 8080...
cd ..\backend
start "Python Backend" cmd /c "pip install -r requirements.txt -q && uvicorn main:app --host 127.0.0.1 --port 8080 --reload"
cd ..\alarm-app

timeout /t 3 /nobreak >nul

:: Start Node mock backend (dashboard regions)
echo [2/3] Starting mock backend on port 3001...
cd backend
start "Mock Backend" cmd /c "npm install && npm start"
cd ..

timeout /t 2 /nobreak >nul

:: Start frontend
echo [3/3] Starting frontend on port 5173...
cd frontend
start "Frontend" cmd /c "npm install && npm run dev"
cd ..

echo.
echo  Python API (Grok): http://localhost:8080
echo  Mock API:          http://localhost:3001
echo  Frontend:          http://localhost:5173
echo.
pause
