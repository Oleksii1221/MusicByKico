from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from src.bot.client import MusicBot
from src.music.player import GuildPlayer

logger = logging.getLogger(__name__)


class MusicCog(commands.Cog):
    def __init__(self, bot: MusicBot) -> None:
        self.bot = bot
        self.music = bot.music_service

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.guild is None:
            await self._safe_reply(
                interaction,
                "Ця команда працює тільки на сервері.",
                ephemeral=True,
            )
            return False
        return True

    async def _safe_reply(
        self,
        interaction: discord.Interaction,
        message: str,
        *,
        ephemeral: bool = False,
    ) -> None:
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=ephemeral)
        else:
            await interaction.response.send_message(message, ephemeral=ephemeral)

    def _get_player(self, interaction: discord.Interaction) -> GuildPlayer | None:
        if interaction.guild is None:
            return None

        voice = interaction.guild.voice_client
        if isinstance(voice, GuildPlayer):
            return voice
        return None

    @app_commands.command(name="play", description="одає трек або плейлист у чергу")
    @app_commands.describe(query="YouTube / YouTube Music URL або пошуковий запит")
    async def play(self, interaction: discord.Interaction, query: str) -> None:
        await interaction.response.defer(thinking=True)

        try:
            player = await self.music.get_or_connect_player(interaction)
            result = await self.music.resolve_query(player, query)

            added_count, title, is_playlist = await self.music.enqueue_search_result(
                player=player,
                search_result=result,
                requested_by=interaction.user.id,
            )

            started = await self.music.ensure_playing(player)

            if is_playlist:
                suffix = " і запуск почався" if started else ""
                await interaction.followup.send(
                    f"📚 одано плейлист **{title}**. Треків: **{added_count}**{suffix}"
                )
            else:
                suffix = " і запуск почався" if started else ""
                await interaction.followup.send(
                    f"➕ одано в чергу: **{title}**{suffix}"
                )

        except Exception as exc:
            logger.exception("/play failed")
            await interaction.followup.send(
                f"❌ е вдалося виконати /play: {exc}",
                ephemeral=True,
            )

    @app_commands.command(name="skip", description="ропускає поточний трек")
    async def skip(self, interaction: discord.Interaction) -> None:
        player = self._get_player(interaction)
        if player is None:
            await self._safe_reply(interaction, "ема активного плеєра.", ephemeral=True)
            return

        ok = await self.music.skip(player)
        if not ok:
            await self._safe_reply(interaction, "араз нічого не грає.", ephemeral=True)
            return

        await self._safe_reply(interaction, "⏭️ Трек пропущено.")

    @app_commands.command(name="pause", description="Ставит трек на паузу")
    async def pause(self, interaction: discord.Interaction) -> None:
        player = self._get_player(interaction)
        if player is None or player.current is None:
            await self._safe_reply(interaction, "ема що ставити на паузу.", ephemeral=True)
            return

        await player.pause(True)
        await self._safe_reply(interaction, "⏸️ ауза.")

    @app_commands.command(name="resume", description="родовжує відтворення")
    async def resume(self, interaction: discord.Interaction) -> None:
        player = self._get_player(interaction)
        if player is None:
            await self._safe_reply(interaction, "ема активного плеєра.", ephemeral=True)
            return

        await player.resume()
        await self._safe_reply(interaction, "▶️ родовжено.")

    @app_commands.command(name="stop", description="упиняє музику і очищає чергу")
    async def stop(self, interaction: discord.Interaction) -> None:
        player = self._get_player(interaction)
        if player is None:
            await self._safe_reply(interaction, "ема активного плеєра.", ephemeral=True)
            return

        await self.music.stop_and_clear(player)
        await self._safe_reply(interaction, "⏹️ упинено. ерга очищена.")

    @app_commands.command(name="disconnect", description="ихід із голосового каналу")
    async def disconnect(self, interaction: discord.Interaction) -> None:
        player = self._get_player(interaction)
        if player is None:
            await self._safe_reply(
                interaction,
                " не підключений до voice channel.",
                ephemeral=True,
            )
            return

        await self.music.disconnect(player)
        await self._safe_reply(interaction, "👋 ідключився від voice channel.")

    @app_commands.command(name="queue", description="оказує поточну чергу")
    async def queue(self, interaction: discord.Interaction) -> None:
        player = self._get_player(interaction)
        if player is None:
            await self._safe_reply(interaction, "ема активного плеєра.", ephemeral=True)
            return

        current = player.current
        current_line = (
            f"**араз:** {current.title} — {current.author}\n\n"
            if current is not None
            else ""
        )
        preview = self.music.queue_preview(player)
        await self._safe_reply(interaction, f"📜 {current_line}{preview}")

    @app_commands.command(name="nowplaying", description="оказує поточний трек")
    async def nowplaying(self, interaction: discord.Interaction) -> None:
        player = self._get_player(interaction)
        if player is None or player.current is None:
            await self._safe_reply(interaction, "араз нічого не грає.", ephemeral=True)
            return

        track = player.current
        await self._safe_reply(
            interaction,
            f"🎶 **{track.title}**\n"
            f"втор: **{track.author}**\n"
            f"URL: {getattr(track, 'uri', None) or 'ема'}",
        )

    @app_commands.command(name="volume", description="мінює гучність")
    @app_commands.describe(value="ід 1 до 1000")
    async def volume(
        self,
        interaction: discord.Interaction,
        value: app_commands.Range[int, 1, 1000],
    ) -> None:
        player = self._get_player(interaction)
        if player is None:
            await self._safe_reply(interaction, "ема активного плеєра.", ephemeral=True)
            return

        player.default_volume = value
        await player.set_volume(value)
        await self._safe_reply(interaction, f"🔊 учність встановлено на **{value}**.")

    @app_commands.command(name="autoplay", description="микає або вимикає autoplay")
    @app_commands.describe(enabled="true = увімкнути, false = вимкнути")
    async def autoplay(self, interaction: discord.Interaction, enabled: bool) -> None:
        player = self._get_player(interaction)
        if player is None:
            await self._safe_reply(interaction, "ема активного плеєра.", ephemeral=True)
            return

        player.autoplay_enabled = enabled
        await self._safe_reply(
            interaction,
            f"♾️ Autoplay {'увімкнено' if enabled else 'вимкнено'}.",
        )

    @app_commands.command(name="clear", description="чищає чергу")
    async def clear(self, interaction: discord.Interaction) -> None:
        player = self._get_player(interaction)
        if player is None:
            await self._safe_reply(interaction, "ема активного плеєра.", ephemeral=True)
            return

        player.queue.clear()
        await self._safe_reply(interaction, "🧹 ергу очищено.")


async def setup(bot: MusicBot) -> None:
    await bot.add_cog(MusicCog(bot))
