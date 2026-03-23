from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any

import discord
import mafic


@dataclass(slots=True)
class TrackSnapshot:
    title: str
    author: str
    uri: str | None
    requested_by: int | None


@dataclass(slots=True)
class GuildPlaybackState:
    guild_id: int
    bound_text_channel_id: int | None = None
    history: deque[TrackSnapshot] = field(default_factory=lambda: deque(maxlen=25))


class GuildPlayer(mafic.Player[discord.Client]):
    def __init__(
        self,
        client: discord.Client,
        channel: discord.abc.Connectable,
        **kwargs: Any,
    ) -> None:
        super().__init__(client, channel, **kwargs)
        self.state = GuildPlaybackState(guild_id=0)
        self.default_volume: int = 75
        self.queue: deque[tuple[mafic.Track, int | None]] = deque()
        self.autoplay_enabled: bool = True
        self.current_requested_by: int | None = None

    def ensure_state(self) -> None:
        if self.guild is not None:
            self.state.guild_id = self.guild.id

    def bind_text_channel(
        self,
        channel: discord.abc.MessageableChannel | discord.TextChannel,
    ) -> None:
        self.state.bound_text_channel_id = getattr(channel, "id", None)

    def remember_current_track(self) -> None:
        current = self.current
        if current is None:
            return

        self.state.history.append(
            TrackSnapshot(
                title=getattr(current, "title", "Unknown"),
                author=getattr(current, "author", "Unknown"),
                uri=getattr(current, "uri", None),
                requested_by=self.current_requested_by,
            )
        )

    @property
    def bound_text_channel_id(self) -> int | None:
        return self.state.bound_text_channel_id