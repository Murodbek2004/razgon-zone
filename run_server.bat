@echo off
chcp 65001 >nul
title RAZGON ZONE - LOCAL SERVER
echo ========================================================
echo    RAZGON ZONE - SERVER LAUNCHER
echo ========================================================
echo.
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment .venv not found.
    pause
    exit /b 1
)

echo Starting Razgon Zone on your PC...
echo WebApp URL: http://localhost:8080
echo.
".venv\Scripts\python.exe" main.py
pause
