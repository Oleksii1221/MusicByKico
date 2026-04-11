from __future__ import annotations

import logging
from typing import Iterable

import discord
import mafic

from src.music.player import GuildPlayer

logger = logging.getLogger(__name__)


class MusicService:
    def __init__(self, default_volume: int) -> None:
        self.default_volume = default_volume

    async def get_or_connect_player(
        self,
        interaction: discord.Interaction,
    ) -> GuildPlayer:
        if interaction.guild is None:
            raise RuntimeError("This command can only be used in a guild.")

        user = interaction.user
        if not isinstance(user, discord.Member):
            raise RuntimeError("Could not resolve member.")

        if user.voice is None or user.voice.channel is None:
            raise RuntimeError("You must be in a voice channel.")

        voice_channel = user.voice.channel
        existing = interaction.guild.voice_client

        if existing is None:
            player = await voice_channel.connect(cls=GuildPlayer, self_deaf=True)
            assert isinstance(player, GuildPlayer)

            player.ensure_state()
            if interaction.channel is not None:
                player.bind_text_channel(interaction.channel)

            player.default_volume = self.default_volume
            await player.set_volume(self.default_volume)
            return player

        if not isinstance(existing, GuildPlayer):
            raise RuntimeError("Voice client exists but is not a GuildPlayer.")

        player = existing
        player.ensure_state()

        if interaction.channel is not None:
            player.bind_text_channel(interaction.channel)

        if player.channel and getattr(player.channel, "id", None) != voice_channel.id:
            await player.disconnect(force=True)
            player = await voice_channel.connect(cls=GuildPlayer, self_deaf=True)
            assert isinstance(player, GuildPlayer)
            player.ensure_state()
            if interaction.channel is not None:
                player.bind_text_channel(interaction.channel)
            player.default_volume = self.default_volume
            await player.set_volume(self.default_volume)

        return player

    async def resolve_query(
        self,
        player: GuildPlayer,
        query: str,
    ) -> list[mafic.Track] | mafic.Playlist:
        cleaned = query.strip()
        if not cleaned:
            raise RuntimeError("Query is empty.")

        if cleaned.startswith(("http://", "https://")):
            result = await player.fetch_tracks(cleaned)
        else:
            result = await player.fetch_tracks(
                cleaned,
                search_type=mafic.SearchType.YOUTUBE_MUSIC,
            )

        if result is None:
            raise RuntimeError("Nothing was found for your query.")

        return result

    async def enqueue_search_result(
        self,
        player: GuildPlayer,
        search_result: list[mafic.Track] | mafic.Playlist,
        requested_by: int,
    ) -> tuple[int, str, bool]:
        if isinstance(search_result, mafic.Playlist):
            added = 0
            for track in search_result.tracks:
                player.queue.append((track, requested_by))
                added += 1
            return added, search_result.name, True

        if not search_result:
            raise RuntimeError("Nothing was found for your query.")

        track = search_result[0]
        player.queue.append((track, requested_by))
        return 1, track.title, False

    async def ensure_playing(self, player: GuildPlayer) -> bool:
        if player.current is not None or player.paused:
            return False

        if not player.queue:
            return False

        next_track, requested_by = player.queue.popleft()
        player.current_requested_by = requested_by
        await player.play(next_track, volume=player.default_volume)
        return True

    async def play_next(self, player: GuildPlayer) -> bool:
        if not player.queue:
            return False

        next_track, requested_by = player.queue.popleft()
        player.current_requested_by = requested_by
        await player.play(next_track, volume=player.default_volume)
        return True

    async def skip(self, player: GuildPlayer) -> bool:
        if player.current is None:
            return False

        await player.stop()
        return True

    async def stop_and_clear(self, player: GuildPlayer) -> None:
        player.queue.clear()
        player.current_requested_by = None
        await player.stop()

    async def disconnect(self, player: GuildPlayer) -> None:
        player.queue.clear()
        player.current_requested_by = None
        await player.disconnect(force=True)

    def queue_preview(self, player: GuildPlayer, limit: int = 10) -> str:
        if not player.queue:
            return "Черга порожня."

        lines: list[str] = []
        entries: Iterable[tuple[mafic.Track, int | None]] = list(player.queue)[:limit]

        for index, (track, _) in enumerate(entries, start=1):
            title = getattr(track, "title", "Unknown")
            author = getattr(track, "author", "Unknown")
            lines.append(f"{index}. {title} — {author}")

        if len(player.queue) > limit:
            lines.append("...")

        return "\n".join(lines)

    async def build_autoplay_seed(self, player: GuildPlayer) -> str | None:
        history = list(player.state.history)
        if not history:
            current = player.current
            if current is None:
                return None
            seed = f"{getattr(current, 'title', '')} {getattr(current, 'author', '')}".strip()
            return seed or None

        recent = history[-3:]
        parts: list[str] = []
        for item in recent:
            parts.append(f"{item.title} {item.author}".strip())

        seed = " ".join(parts).strip()
        return seed or None

    async def fill_autoplay(self, player: GuildPlayer) -> bool:
        if not player.autoplay_enabled:
            return False

        seed = await self.build_autoplay_seed(player)
        if not seed:
            return False

        try:
            result = await player.fetch_tracks(
                seed,
                search_type=mafic.SearchType.YOUTUBE_MUSIC,
            )
        except Exception:
            logger.exception("Autoplay fetch failed")
            return False

        if not result or isinstance(result, mafic.Playlist):
            return False

        track = result[0]
        player.queue.append((track, None))
        return True