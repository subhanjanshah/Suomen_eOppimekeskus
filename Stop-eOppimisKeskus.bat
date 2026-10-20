@echo off
cd /d "%~dp0"
title Stop eOppimisKeskus

echo Stopping eOppimisKeskus...

docker compose down

if errorlevel 1 (
    echo.
    echo Failed to stop eOppimisKeskus.
    echo Please check Docker Desktop.
    pause
    exit /b 1
)

echo.
echo eOppimisKeskus stopped successfully.

exit