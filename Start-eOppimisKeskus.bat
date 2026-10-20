@echo off
setlocal
cd /d "%~dp0"
title eOppimisKeskus Launcher

echo Starting eOppimisKeskus...

where docker >nul 2>&1
if errorlevel 1 (
    echo Docker was not found.
    echo Please install Docker Desktop first.
    pause
    exit /b 1
)

docker info >nul 2>&1
if errorlevel 1 (
    echo Starting Docker Desktop...
    if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" (
        start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
    ) else (
        echo Please open Docker Desktop manually.
        pause
        exit /b 1
    )
)

echo Waiting for Docker to become ready...
set /a attempts=0

:wait_docker
docker info >nul 2>&1
if not errorlevel 1 goto docker_ready

set /a attempts+=1
if %attempts% GEQ 60 (
    echo Docker did not become ready.
    pause
    exit /b 1
)

timeout /t 3 /nobreak >nul
goto wait_docker

:docker_ready
echo Starting application...
docker compose up -d --build
if errorlevel 1 (
    echo Failed to start the application.
    pause
    exit /b 1
)

echo Waiting for the application...
set /a attempts=0

:wait_app
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:8501/_stcore/health' -UseBasicParsing -TimeoutSec 3; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 goto app_ready

set /a attempts+=1
if %attempts% GEQ 60 (
    echo Application is taking longer than expected.
    echo Check Docker Desktop or run: docker compose logs
    pause
    exit /b 1
)

timeout /t 3 /nobreak >nul
goto wait_app

:app_ready
echo Opening eOppimisKeskus...
start "" "http://localhost:8501"
echo Application started successfully.
exit /b 0