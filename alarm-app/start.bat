@echo off
echo Starting Ukraine Alarm Shield...
echo.

:: Start backend
echo [1/2] Starting backend on port 3001...
cd backend
start "Backend" cmd /c "npm install && npm start"
cd ..

:: Wait a moment for backend to start
timeout /t 3 /nobreak >nul

:: Start frontend
echo [2/2] Starting frontend on port 5173...
cd frontend
start "Frontend" cmd /c "npm install && npm run dev"
cd ..

echo.
echo  Backend:  http://localhost:3001
echo  Frontend: http://localhost:5173
echo.
pause
