@echo off
setlocal ENABLEEXTENSIONS

cd /d "%~dp0"
title MusicBot Stopper

set "COMPOSE_CMD="

docker compose version >nul 2>nul
if not errorlevel 1 (
    set "COMPOSE_CMD=docker compose"
)

if not defined COMPOSE_CMD (
    docker-compose version >nul 2>nul
    if not errorlevel 1 (
        set "COMPOSE_CMD=docker-compose"
    )
)

if not defined COMPOSE_CMD (
    echo [ERROR] Docker Compose не знайдено.
    pause
    exit /b 1
)

call %COMPOSE_CMD% -f deploy\docker-compose.yml down
pause