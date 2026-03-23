from __future__ import annotations

import asyncio
import logging
from urllib.parse import urlparse

import discord
import mafic
from discord.ext import commands

from src.core.config import Settings, get_settings
from src.music.player import GuildPlayer
from src.music.service import MusicService
from src.notifications.telegram import TelegramNotifier

logger = logging.getLogger(__name__)


class MusicBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.guilds = True
        intents.voice_states = True
        intents.message_content = False

        self.settings: Settings = get_settings()

        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=intents,
            application_id=self.settings.discord_app_id or None,
        )

        self.pool: mafic.NodePool[discord.Client] | None = None
        self.music_service = MusicService(default_volume=self.settings.default_volume)
        self.notifier = TelegramNotifier(
            bot_token=self.settings.telegram_bot_token,
            chat_id=self.settings.telegram_chat_id,
        )

        self._lavalink_connected = False
        self._startup_lock = asyncio.Lock()

    async def setup_hook(self) -> None:
        self.pool = mafic.NodePool(self)
        await self.load_extension("src.bot.cogs.music")

        if self.settings.auto_sync_commands:
            synced = await self.tree.sync()
            logger.info("Synced %s application commands.", len(synced))

    async def connect_lavalink(self) -> None:
        if self.pool is None:
            raise RuntimeError("NodePool was not initialized.")

        parsed = urlparse(self.settings.lavalink_uri)
        host = parsed.hostname or "localhost"
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        secure = parsed.scheme == "https"

        last_error: Exception | None = None

        for attempt in range(1, 11):
            try:
                await self.pool.create_node(
                    host=host,
                    port=port,
                    label=self.settings.lavalink_node_id,
                    password=self.settings.lavalink_password,
                    secure=secure,
                    player_cls=GuildPlayer,
                )
                logger.info("Connected to Lavalink node: %s", self.settings.lavalink_node_id)
                self._lavalink_connected = True
                return
            except Exception as exc:
                last_error = exc
                logger.warning("Lavalink connect attempt %s/10 failed: %s", attempt, exc)
                await asyncio.sleep(3)

        raise RuntimeError(f"Could not connect to Lavalink: {last_error}")

    async def on_ready(self) -> None:
        async with self._startup_lock:
            if not self._lavalink_connected:
                await self.connect_lavalink()

        if self.user is not None:
            logger.info("Logged in as %s (%s)", self.user, self.user.id)
        else:
            logger.info("Bot is ready, but self.user is None.")

    async def on_node_ready(self, node: mafic.Node[discord.Client]) -> None:
        logger.info("Mafic node ready: %s", node.label)

    async def on_node_unavailable(self, node: mafic.Node[discord.Client]) -> None:
        logger.warning("Mafic node unavailable: %s", node.label)
        await self.notifier.send(f"⚠️ MusicBot node unavailable\nNode: {node.label}")

    async def on_track_start(self, event: mafic.TrackStartEvent[GuildPlayer]) -> None:
        player = event.player
        if not isinstance(player, GuildPlayer):
            return

        player.ensure_state()
        channel_id = player.bound_text_channel_id
        if not channel_id or not player.guild:
            return

        channel = player.guild.get_channel(channel_id)
        if channel is None or not isinstance(channel, discord.TextChannel):
            return

        track = event.track
        await channel.send(f"▶️ Зараз грає: **{track.title}** — {track.author}")

    async def on_track_end(self, event: mafic.TrackEndEvent[GuildPlayer]) -> None:
        player = event.player
        if not isinstance(player, GuildPlayer):
            return

        player.remember_current_track()

        started = await self.music_service.play_next(player)
        if started:
            return

        filled = await self.music_service.fill_autoplay(player)
        if filled:
            await self.music_service.play_next(player)

    async def on_track_exception(self, event: mafic.TrackExceptionEvent[GuildPlayer]) -> None:
        track = getattr(event, "track", None)
        title = getattr(track, "title", "Unknown")
        logger.warning("Track exception: %s | %s", title, event.exception)

        await self.notifier.send(
            f"⚠️ MusicBot track exception\n"
            f"Track: {title}\n"
            f"Error: {event.exception}"
        )

    async def on_websocket_closed(self, event: mafic.WebSocketClosedEvent[GuildPlayer]) -> None:
        logger.warning(
            "Voice websocket closed | code=%s by_discord=%s reason=%s",
            event.code,
            event.by_discord,
            event.reason,
        )

        await self.notifier.send(
            f"⚠️ MusicBot voice websocket closed\n"
            f"Code: {event.code}\n"
            f"Reason: {event.reason}"
        )