@echo off
chcp 65001 >nul
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"

set "PROJECT_DIR=%~dp0"
set "COMPOSE_FILE=deploy\docker-compose.yml"
set "ENV_FILE=.env"
set "LOG_DIR=%PROJECT_DIR%logs"
set "LOG_FILE=%LOG_DIR%\autostart.log"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" >nul 2>nul

call :log ==================================================
call :log MusicBot autostart script started
call :log Project dir: %PROJECT_DIR%

REM Small startup delay so Windows, network and Docker Desktop have time to wake up
timeout /t 20 /nobreak >nul

if not exist "%ENV_FILE%" (
    call :log ERROR: .env file not found
    exit /b 1
)

if not exist "%COMPOSE_FILE%" (
    call :log ERROR: deploy\docker-compose.yml not found
    exit /b 1
)

where docker >nul 2>nul
if errorlevel 1 (
    call :log ERROR: docker command not found in PATH
    exit /b 1
)

set "COMPOSE_CMD="
docker compose version >nul 2>nul
if not errorlevel 1 set "COMPOSE_CMD=docker compose"

if not defined COMPOSE_CMD (
    docker-compose version >nul 2>nul
    if not errorlevel 1 set "COMPOSE_CMD=docker-compose"
)

if not defined COMPOSE_CMD (
    call :log ERROR: Docker Compose not found
    exit /b 1
)

call :log Using compose command: %COMPOSE_CMD%

REM Try to start Docker Desktop if engine is not ready yet
docker info >nul 2>nul
if errorlevel 1 (
    call :log Docker engine is not ready, trying to start Docker Desktop
    call :start_docker_desktop
)

REM Wait up to ~5 minutes for Docker Engine
set /a WAIT_COUNT=0
:wait_docker
docker info >nul 2>nul
if not errorlevel 1 goto docker_ready

set /a WAIT_COUNT+=1
if !WAIT_COUNT! geq 60 (
    call :log ERROR: Docker engine did not become ready in time
    exit /b 1
)

call :log Waiting for Docker engine... attempt !WAIT_COUNT!/60
timeout /t 5 /nobreak >nul
goto wait_docker

:docker_ready
call :log Docker engine is ready

REM If bot container is already running, do nothing
for /f "delims=" %%i in ('docker ps --filter "name=musicbot-bot" --filter "status=running" --format "{{.Names}}" 2^>nul') do (
    if /I "%%i"=="musicbot-bot" (
        call :log musicbot-bot is already running, nothing to do
        exit /b 0
    )
)

call :log Starting containers...
call %COMPOSE_CMD% -f "%COMPOSE_FILE%" up -d >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    call :log ERROR: docker compose up -d failed
    exit /b 1
)

REM Wait a bit and verify containers
timeout /t 10 /nobreak >nul

set "BOT_RUNNING="
for /f "delims=" %%i in ('docker ps --filter "name=musicbot-bot" --filter "status=running" --format "{{.Names}}" 2^>nul') do (
    if /I "%%i"=="musicbot-bot" set "BOT_RUNNING=1"
)

set "LAVALINK_RUNNING="
for /f "delims=" %%i in ('docker ps --filter "name=musicbot-lavalink" --filter "status=running" --format "{{.Names}}" 2^>nul') do (
    if /I "%%i"=="musicbot-lavalink" set "LAVALINK_RUNNING=1"
)

if not defined LAVALINK_RUNNING (
    call :log ERROR: musicbot-lavalink is not running after startup
    exit /b 1
)

if not defined BOT_RUNNING (
    call :log ERROR: musicbot-bot is not running after startup
    exit /b 1
)

call :log SUCCESS: musicbot-bot and musicbot-lavalink are running
exit /b 0

:start_docker_desktop
if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" (
    start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
    call :log Started Docker Desktop from %ProgramFiles%\Docker\Docker\Docker Desktop.exe
    exit /b 0
)

if exist "%LocalAppData%\Programs\Docker\Docker\Docker Desktop.exe" (
    start "" "%LocalAppData%\Programs\Docker\Docker\Docker Desktop.exe"
    call :log Started Docker Desktop from %LocalAppData%\Programs\Docker\Docker\Docker Desktop.exe
    exit /b 0
)

call :log WARNING: Docker Desktop.exe not found in common locations
exit /b 0

:log
set "STAMP=%date% %time%"
echo [%STAMP%] %*>> "%LOG_FILE%"
echo [%STAMP%] %*
exit /b 0