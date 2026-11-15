@echo off
title AgriVision AI - Unified Server Launcher
echo ========================================================
echo   Starting AgriVision AI Unified Full-Stack Server
echo   (Frontend + Backend REST API + CNN Crop Disease + ML)
echo ========================================================

set "PY=C:\Users\KANNAN\.local\bin\python3.11.exe"
if not exist "%PY%" (
    set "PY=python"
)

echo Starting Unified Server on port 8000...
echo Opening browser to http://127.0.0.1:8000/login.html in 2 seconds...
cd /d "%~dp0backend"

REM Automatically open default web browser after server boots
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:8000/login.html"

"%PY%" manage.py runserver 127.0.0.1:8000
