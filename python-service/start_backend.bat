@echo off
title Healthcare System — Backend
echo Starting backend server...

if exist venv_offline\Scripts\activate (
    call venv_offline\Scripts\activate
) else if exist venv311\Scripts\activate (
    call venv311\Scripts\activate
) else (
    echo ERROR: No virtual environment found.
    echo Expected "venv_offline" or "venv311" folder in this directory.
    pause
    exit /b 1
)

python main.py
pause
