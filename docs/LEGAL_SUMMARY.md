# Legal Summary — MusicByKico

## Files Analyzed

| File | Purpose |
|------|---------|
| `src/bot/client.py` | Main bot logic, Discord intents, event handlers |
| `src/bot/cogs/playback.py` | Slash commands: /play, /playnext, /skip, /back, /pause, /resume, /stop |
| `src/bot/cogs/queue.py` | Slash commands: /queue, /nowplaying, /remove, /clear |
| `src/bot/cogs/settings.py` | Slash commands: /volume, /autoplay, /disconnect |
| `src/music/player.py` | GuildPlayer — in-memory queue, history, state |
| `src/music/service.py` | MusicService — search, enqueue, autoplay logic |
| `src/core/config.py` | Settings loaded from .env, no persistent storage |
| `src/notifications/telegram.py` | Optional Telegram error alerts to operator |
| `pyproject.toml` | Dependencies: discord.py, mafic, aiohttp, PyNaCl, python-dotenv |
| `deploy/docker-compose.yml` | Infrastructure: bot + lavalink containers |
| `deploy/docker/lavalink/application.yml` | Lavalink config, YouTube plugin |
| `.env.example` | Environment variables template |
| `README.md` | Project description |

---

## Data Processing Facts (confirmed from source code)

### Data the Bot DOES process (in memory only)
| Data | Where | How long |
|------|-------|----------|
| Discord User IDs | `player.current_requested_by`, queue tuples | Duration of session |
| Discord Guild IDs | `GuildPlaybackState.guild_id` | Duration of session |
| Discord Text Channel IDs | `GuildPlaybackState.bound_text_channel_id` | Duration of session |
| Discord Voice Channel IDs | `player.channel` (mafic) | Duration of session |
| Search query strings | `resolve_query()` → forwarded to Lavalink/YouTube | Not stored, single request |
| Track title, author, URI | `TrackSnapshot`, queue deque | Max 25 items in history, cleared on disconnect |

### Data the Bot does NOT process
- ❌ `message_content` intent — **explicitly False** in `client.py` line 24
- ❌ No database (no SQLite, PostgreSQL, MySQL, Redis, or any DB driver in dependencies)
- ❌ No files written to disk (no open(), no json.dump(), no logging to file)
- ❌ No usernames, avatars, email addresses, or profile data
- ❌ No analytics, tracking pixels, or third-party monitoring SDKs
- ❌ No payment processing

### Logging
Standard Python `logging` module to stdout/stderr only. No persistent log files.
Log level configurable via `LOG_LEVEL` env var. No user-identifiable data is logged beyond track titles.

---

## Third-Party Services Found

| Service | How Used | Their Privacy Policy |
|---------|----------|----------------------|
| **Discord API** | Core platform, slash commands, voice | https://discord.com/privacy |
| **YouTube / YouTube Music** | Audio resolution via Lavalink plugin | https://policies.google.com/privacy |
| **Lavalink** | Self-hosted audio server (Docker container) | Self-hosted, no third-party data flow |
| **Telegram Bot API** | Optional operator-only error alerts | https://telegram.org/privacy |

---

## TODO Items Left for Manual Completion

All known placeholders have been replaced. No remaining TODOs in HTML files.

---

## What to Manually Verify Before Publishing

- [ ] Confirm no log files are written to disk in your production deployment
- [ ] If you add any database or persistent storage in the future, update `privacy.html` section 5
- [ ] If the Bot is ever used commercially or monetized, terms.html needs a payment/subscription section
- [ ] Confirm Telegram alerts contain only technical data and no user-identifiable content
- [ ] Review YouTube's ToS compliance for your specific use case
