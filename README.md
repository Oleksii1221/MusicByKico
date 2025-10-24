# 🎵 MusicByKico — Discord Music Bot  
*A modern Python-based Discord bot for streaming high-quality music from YouTube with playlist and autoplay support.*  
*Сучасний Discord-бот на Python для потокового відтворення музики з YouTube із підтримкою плейлистів та автоматичних рекомендацій.*

---

## 🚀 Features / Основні можливості

- 🎧 Plays **YouTube videos** and **playlists**
- 🔁 **Autoplay** — continues playback with YouTube’s recommended songs  
- 🧠 **Smart queue management** (skip, pause, resume, clear)
- 🔊 **Real-time playback control** via Discord Slash Commands  
- 🎶 Works with **text search or YouTube links**
- 🪄 Simple setup, lightweight, and easy to host on any server
- 💡 **Fully asynchronous** and optimized for low latency streaming

---

## 🧰 Requirements / Вимоги

Before running the bot, make sure you have these installed:  
Перед запуском переконайтесь, що встановлено:

```bash
sudo apt update
sudo apt install -y python3 python3-pip ffmpeg
```

Then install Python libraries:  
Далі встановіть необхідні бібліотеки Python:

```bash
pip install -U discord.py yt-dlp pynacl python-dotenv
```

---

## ⚙️ Setup / Налаштування

1. **Create a Discord bot token**  
   Go to [Discord Developer Portal](https://discord.com/developers/applications), create a new bot and copy its token.

2. **Create `.env` file**  
   Створіть файл `.env` у корені проєкту:

   ```env
   DISCORD_TOKEN=your_discord_token_here
   ```

3. **Run the bot**  
   Запуск через Python:

   ```bash
   python bot.py
   ```

4. **Invite bot to your server**  
   Use this OAuth2 URL template (replace `YOUR_CLIENT_ID`):  
   Використайте це посилання, замінивши `YOUR_CLIENT_ID`:

   ```
   https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=3145728&scope=bot%20applications.commands
   ```

---

## 💻 Commands / Команди

| Command | Description (EN) | Опис (UA) |
|----------|------------------|-----------|
| `/join` | Connects bot to your current voice channel | Підключає бота до вашого голосового каналу |
| `/leave` | Disconnects bot | Від’єднує бота |
| `/play <url or search>` | Plays YouTube video/playlist or searches by name | Відтворює відео/плейлист або шукає трек за назвою |
| `/pause` | Pauses current track | Ставит поточний трек на паузу |
| `/resume` | Resumes playback | Продовжує відтворення |
| `/skip` | Skips current track | Пропускає поточний трек |
| `/stop` | Stops playback and clears queue | Зупиняє відтворення та очищає чергу |
| `/queue` | Shows queued songs | Показує чергу треків |
| `/now` | Shows currently playing song | Показує трек, який зараз грає |
| `/autoplay on/off` | Enables or disables autoplay (YouTube recommendations) | Вмикає або вимикає автопродовження за рекомендаціями |

---

## 🧠 How Autoplay Works / Як працює автопродовження

When the queue is empty, the bot automatically fetches a **recommended track** from YouTube based on the last played video.  
Якщо черга порожня, бот автоматично підбирає **рекомендовану пісню** на основі попереднього треку на YouTube.  

If YouTube doesn’t return related videos, the bot falls back to a **title-based search**.  
Якщо YouTube не повертає пов’язані відео — бот шукає схожий трек за назвою.

---

## 🧩 Folder Structure / Структура проєкту

```
MusicByKico/
│
├── bot.py              # Main bot logic
├── .env                # Discord token
├── requirements.txt    # (optional) Dependencies
└── README.md           # This file
```

---

## 🧾 Example `.env` / Приклад `.env`

```env
DISCORD_TOKEN=MzUwOTk1NTIzMDE1NzQ3NTY5.GF3...your_token
```

---

## 💡 Example Command Usage / Приклад використання команд

```bash
/play https://www.youtube.com/watch?v=dQw4w9WgXcQ
/play lo-fi chill beats
/queue
/autoplay on
```

---

## 🔧 Hosting on a Server / Хостинг на сервері

For permanent hosting on Linux (Ubuntu/Debian), create a systemd service:  
Для постійної роботи на сервері Linux створіть systemd-сервіс:

```bash
sudo nano /etc/systemd/system/musicbykico.service
```

Insert:
```ini
[Unit]
Description=MusicByKico Discord Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/MusicByKico
ExecStart=/usr/bin/python3 /path/to/MusicByKico/bot.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Then run:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now musicbykico.service
```

---

## 🧠 Technologies Used / Використані технології

| Technology | Purpose | Призначення |
|-------------|----------|-------------|
| **Python 3.10+** | Core language | Основна мова |
| **discord.py** | Discord interaction | Взаємодія з Discord |
| **yt-dlp** | YouTube audio extraction | Отримання аудіо з YouTube |
| **FFmpeg** | Audio processing | Обробка аудіо потоку |
| **PyNaCl** | Voice channel encryption | Голосове з’єднання |

---

## 🪄 Example Bot Output / Приклад роботи

```
Logged in as MusicByKico#1234
▶️ Playing: Lo-Fi Beats to Relax
🔁 Autoplay: ON
⏭️ Skipped track
```

---

## 🧑‍💻 Contributing / Внесок у проєкт

1. Fork the repository  
2. Create a new branch (`feature/your-feature`)  
3. Commit your changes  
4. Submit a Pull Request

1. Форкніть репозиторій  
2. Створіть нову гілку (`feature/your-feature`)  
3. Зробіть коміт  
4. Відправте Pull Request

---

## 📜 License / Ліцензія

MIT License © 2025 [Kico](https://github.com/yourusername)

---

## ❤️ Support / Підтримка

If you like this project — give it a ⭐ on GitHub!  
Якщо сподобався проєкт — поставте ⭐ на GitHub!

---

**Author / Автор:** [Kico](https://github.com/yourusername)  
**Project:** MusicByKico  
**Language / Мова:** Python 3.10+
