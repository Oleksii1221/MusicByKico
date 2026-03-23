@echo off
chcp 65001 >nul
setlocal ENABLEEXTENSIONS

cd /d "%~dp0"
title MusicBot Launcher

echo ==========================================
echo         MusicBot startup script
echo ==========================================
echo.

if not exist ".env" (
    if exist ".env.example" (
        echo [INFO] Файл .env не знайдено, створюю копію з .env.example
        copy /Y ".env.example" ".env" >nul
        echo [OK] Файл .env створено.
        echo [INFO] Тепер відкрий .env і заповни токени.
        echo.
        pause
        exit /b 0
    ) else (
        echo [ERROR] Файл .env не знайдено.
        echo Також не знайдено .env.example
        echo.
        pause
        exit /b 1
    )
)

if not exist "deploy\docker-compose.yml" (
    echo [ERROR] Не знайдено deploy\docker-compose.yml
    echo Перевір структуру проекту.
    echo.
    pause
    exit /b 1
)

where docker >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Docker не встановлений або не доданий у PATH.
    echo.
    pause
    exit /b 1
)

docker info >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Docker Desktop не запущений.
    echo Запусти Docker Desktop і повтори.
    echo.
    pause
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
    echo [ERROR] Не знайдено Docker Compose.
    echo.
    pause
    exit /b 1
)

echo [INFO] Використовую: %COMPOSE_CMD%
echo [INFO] Запускаю MusicBot + Lavalink...
echo.

call %COMPOSE_CMD% -f deploy\docker-compose.yml up --build -d
if errorlevel 1 (
    echo.
    echo [ERROR] Не вдалося запустити контейнери.
    echo.
    pause
    exit /b 1
)

echo.
echo [OK] Все запущено.
echo.
call %COMPOSE_CMD% -f deploy\docker-compose.yml ps

echo.
echo Команди:
echo   Логи бота:      %COMPOSE_CMD% -f deploy\docker-compose.yml logs -f bot
echo   Логи lavalink:  %COMPOSE_CMD% -f deploy\docker-compose.yml logs -f lavalink
echo   Зупинити все:   %COMPOSE_CMD% -f deploy\docker-compose.yml down
echo.
pause
exit /b 0