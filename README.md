# MusicBot

Професійний Discord music bot на Python + discord.py + Wavelink + Lavalink.

## Що вже є

- slash-команди
- окремий player і окрема черга для кожного Discord сервера
- автоматичне підключення в voice channel користувача
- відтворення YouTube / YouTube Music URL або пошуку
- playlist support
- autoplay
- queue / nowplaying / skip / stop / volume / disconnect
- Telegram alerts на помилки voice/source
- Docker-ready структура

## Команди

- `/play <query>`
- `/skip`
- `/pause`
- `/resume`
- `/stop`
- `/disconnect`
- `/queue`
- `/nowplaying`
- `/volume <1..1000>`
- `/autoplay <true|false>`
- `/clear`

## Локальний запуск

### 1. Створи `.env`

Скопіюй `.env.example` в `.env` і заповни значення.

### 2. Запусти Lavalink і бота через Docker

```bash
docker compose -f deploy/docker-compose.yml up --build -d