from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(slots=True)
class Settings:
    discord_token: str
    discord_app_id: int
    lavalink_uri: str
    lavalink_password: str
    lavalink_node_id: str
    default_volume: int
    auto_sync_commands: bool
    log_level: str
    telegram_bot_token: str | None
    telegram_chat_id: str | None


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def get_settings() -> Settings:
    token = os.getenv("DISCORD_TOKEN", "").strip()
    app_id = os.getenv("DISCORD_APP_ID", "0").strip()

    if not token:
        raise RuntimeError("DISCORD_TOKEN is missing")

    return Settings(
        discord_token=token,
        discord_app_id=int(app_id or 0),
        lavalink_uri=os.getenv("LAVALINK_URI", "http://localhost:2333").strip(),
        lavalink_password=os.getenv("LAVALINK_PASSWORD", "change_me_please").strip(),
        lavalink_node_id=os.getenv("LAVALINK_NODE_ID", "main-node").strip(),
        default_volume=max(1, min(1000, int(os.getenv("DEFAULT_VOLUME", "75")))),
        auto_sync_commands=_to_bool(os.getenv("AUTO_SYNC_COMMANDS", "true"), True),
        log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper(),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", "").strip() or None,
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", "").strip() or None,
    )