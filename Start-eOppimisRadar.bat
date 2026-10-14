
@echo off
cd /d "%~dp0"

docker compose up -d

if errorlevel 1 (
    echo Failed to start eOppimisRadar.
    echo Make sure Docker Desktop is running.
    pause
    exit /b 1
)

start "" "http://localhost:8501"
exit
