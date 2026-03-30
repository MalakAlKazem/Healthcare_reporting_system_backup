@echo off
title Healthcare Reporting System
echo ================================
echo  Healthcare Reporting System
echo ================================
echo.
echo Starting backend...
cd /d "%~dp0python-service"

if exist venv_offline\Scripts\activate (
    start "Backend" cmd /k "call venv_offline\Scripts\activate && python main.py"
) else if exist venv311\Scripts\activate (
    start "Backend" cmd /k "call venv311\Scripts\activate && python main.py"
) else (
    echo ERROR: No virtual environment found.
    pause
    exit /b 1
)

echo Starting frontend...
cd /d "%~dp0frontend"
start "Frontend" cmd /k "node_modules\.bin\vite.cmd"

echo.
echo Waiting for frontend to be ready on port 3000...
:WAIT_LOOP
timeout /t 2 /nobreak >nul
powershell -Command "try { (New-Object Net.Sockets.TcpClient('localhost', 3000)).Close(); exit 0 } catch { exit 1 }" >nul 2>&1
if errorlevel 1 goto WAIT_LOOP

echo Opening browser...
start "" "http://localhost:3000"

echo.
echo Both services are running.
echo Close the Backend and Frontend windows to stop the system.
pause
