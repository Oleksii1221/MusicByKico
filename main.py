import os
import asyncio
from dataclasses import dataclass
from typing import Optional, List, Union

import discord
from discord import app_commands
from discord.ext import commands
from yt_dlp import YoutubeDL
from dotenv import load_dotenv
import itertools


load_dotenv()

YDL_OPTS_BASE = {
    "format": "bestaudio/best",
    "noplaylist": False,          # дозволяємо плейлисти
    "quiet": True,
    "default_search": "ytsearch", # дозволяє пошук по тексту
    "skip_download": True,
    "extract_flat": False,        # для отримання прямого потоку
    "cachedir": False,
    "source_address": "0.0.0.0",
    "postprocessors": [],
}

FFMPEG_OPTS = {
    "before_options": "-nostdin",
    "options": "-vn"
}

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents)

RUSSIAN_LANGUAGE_CODES = {"ru", "rus"}

@dataclass
class Track:
    url: str             # оригінальний URL або пошуковий запит
    title: str
    webpage_url: str     # сторінка відео (для пов’язаних)
    stream_url: str      # прямий аудіопотік
    duration: Optional[int] = None
    uploader: Optional[str] = None
    id: Optional[str] = None
    language: Optional[str] = None  # мова треку (наприклад "ru", "uk", "en")


def is_russian_track(track: Track) -> bool:
    """Повертає True, якщо трек визначено як російськомовний контент."""
    if track.language and track.language.lower() in RUSSIAN_LANGUAGE_CODES:
        return True
    return False

class YTDLP:
    def __init__(self):
        self.ydl = YoutubeDL(YDL_OPTS_BASE)

    def extract(self, query: str):
        """Повертає info_dict для відео/плейлиста/пошуку."""
        return self.ydl.extract_info(query, download=False)

    def build_track(self, info) -> Track:
        # для adaptive форматів yt-dlp віддає 'url' прямого потоку
        stream_url = info.get("url")
        if not stream_url:
            # інколи потрібен повторний вибір формату
            with YoutubeDL({**YDL_OPTS_BASE, "format": "bestaudio/best"}) as y2:
                info2 = y2.process_ie_result(info, download=False)
                stream_url = info2.get("url")

        return Track(
            url=info.get("original_url") or info.get("webpage_url") or info.get("url"),
            title=info.get("title", "Unknown"),
            webpage_url=info.get("webpage_url") or info.get("url", ""),
            stream_url=stream_url,
            duration=info.get("duration"),
            uploader=info.get("uploader"),
            id=info.get("id"),
            language=info.get("language"),
        )

    def expand_input(self, query_or_url: str) -> List[Track]:
        """Приймає URL/пошук. Повертає список треків (1 або багато, якщо плейлист)."""
        info = self.extract(query_or_url)
        tracks: List[Track] = []

        # плейлист або пошуковий список
        if info.get("_type") == "playlist" or "entries" in info:
            entries = info.get("entries") or []
            # для пошуку беремо перше (ytsearchN)
            if info.get("ie_key", "").lower().startswith("youtubesearch"):
                entries = entries[:1]
            for e in entries:
                if not e:
                    continue
                if e.get("_type") == "url":
                    # інколи повертається "url" без деталей — витягнемо вдруге
                    e = self.extract(e["url"])
                # нормалізація формату та отримання stream_url
                if "url" not in e:
                    e = self.ydl.process_ie_result(e, download=False)
                tracks.append(self.build_track(e))
        else:
            # одиночне відео
            tracks.append(self.build_track(info))

        return tracks

    def get_related(self, video_webpage_url: str, skip_russian: bool = False) -> Optional[Track]:
        """
        Спроба дістати пов’язані (recommended) відео зі сторінки.
        Якщо yt-dlp не поверне related, робимо пошук за назвою.
        Якщо skip_russian=True, пропускає треки російською мовою (для автопродовження).
        """
        info = None
        try:
            info = self.extract(video_webpage_url)
            # yt-dlp часто кладе рекомендовані сюди:
            related = info.get("related_videos") or info.get("related") or []
            for r in related:
                vid = r.get("id") or r.get("url")
                if not vid:
                    continue
                candidate = f"https://www.youtube.com/watch?v={vid}" if len(vid) == 11 else vid
                tr = self.expand_input(candidate)
                if tr:
                    if skip_russian and is_russian_track(tr[0]):
                        continue
                    return tr[0]
        except Exception:
            pass

        # Фолбек: пошук за назвою + uploader
        title = info.get("title") if info else None
        uploader = info.get("uploader") if info else None
        if title:
            q = f"ytsearch1:{title} {uploader or ''}"
            try:
                tr = self.expand_input(q)
                if tr:
                    if skip_russian and is_russian_track(tr[0]):
                        return None
                    return tr[0]
            except Exception:
                pass

        return None

class GuildPlayer:
    def __init__(self, guild: discord.Guild):
        self.guild = guild
        self.queue: asyncio.Queue[Track] = asyncio.Queue()
        self.current: Optional[Track] = None
        self.next_event = asyncio.Event()
        self.autoplay = False
        self.lock = asyncio.Lock()
        self.audio_task: Optional[asyncio.Task] = None
        self.yt = YTDLP()
        self.disconnect_task: Optional[asyncio.Task] = None
        self.text_channel: Optional[discord.TextChannel] = None

    async def ensure_voice(self, interaction: discord.Interaction):
        if not interaction.user.voice or not interaction.user.voice.channel:
            raise RuntimeError("Зайдіть у голосовий канал.")
        vc = interaction.guild.voice_client
        if vc and vc.channel == interaction.user.voice.channel:
            return vc
        if vc and vc.channel != interaction.user.voice.channel:
            await vc.move_to(interaction.user.voice.channel)
            return vc
        return await interaction.user.voice.channel.connect(self_deaf=True)

    async def add(self, tracks: List[Track]):
        for t in tracks:
            await self.queue.put(t)

    def _play_source(self, vc: discord.VoiceClient, track: Track):
        def after_play(err):
            if err:
                print(f"Player error: {err}")
            self.next_event.set()

        source = discord.FFmpegPCMAudio(track.stream_url, **FFMPEG_OPTS)
        vc.play(source, after=after_play)

    async def player_loop(self, vc: discord.VoiceClient, channel: discord.TextChannel):
        self.text_channel = channel
        while True:
            self.next_event.clear()
            # поточний трек: з черги або з autoplay
            if self.queue.empty() and self.autoplay and self.current:
                # беремо рекомендацію, пропускаємо російськомовні треки
                rel = self.yt.get_related(self.current.webpage_url, skip_russian=True)
                if rel:
                    await self.queue.put(rel)

            self.current = await self.queue.get()
            await channel.send(f"▶️ **Грає:** {self.current.title}")

            self._play_source(vc, self.current)
            await self.next_event.wait()

            # Якщо зупинено вручну — вийдемо із циклу
            if not vc.is_connected():
                break

    async def start_if_needed(self, vc: discord.VoiceClient, channel: discord.TextChannel):
        self.text_channel = channel
        if self.audio_task and not self.audio_task.done():
            return
        self.audio_task = asyncio.create_task(self.player_loop(vc, channel))

players: dict[int, GuildPlayer] = {}

def get_player(guild: discord.Guild) -> GuildPlayer:
    if guild.id not in players:
        players[guild.id] = GuildPlayer(guild)
    return players[guild.id]


async def _auto_disconnect_timer(gp: GuildPlayer, vc: discord.VoiceClient):
    """Від'єднує бота після 5 хвилин порожнього голосового каналу."""
    await asyncio.sleep(300)
    if not vc.is_connected():
        return
    channel = vc.channel
    human_members = [m for m in channel.members if not m.bot]
    if len(human_members) == 0:
        if gp.text_channel:
            await gp.text_channel.send("👋 Нікого немає в каналі вже 5 хвилин — від'єднуюсь.")
        await vc.disconnect(force=True)
        if gp.audio_task and not gp.audio_task.done():
            gp.audio_task.cancel()


# --------- SLASH КОМАНДИ ---------

@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
    except Exception as e:
        print("Slash sync error:", e)

    print(f"Logged in as {bot.user} (ID: {bot.user.id})")

    # Циклічний список статусів
    statuses = itertools.cycle([
        discord.Activity(type=discord.ActivityType.watching, name="YouTube рекомендації 🎧"),
        discord.Game(name="/join")
    ])

    # Безкінечний цикл зміни статусу
    while True:
        await bot.change_presence(activity=next(statuses))
        await asyncio.sleep(10)  # міняє кожні 10 секунд

@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    """Автовідключення, якщо голосовий канал порожній протягом 5 хвилин."""
    guild = member.guild
    vc = guild.voice_client
    if not vc or member.bot:
        return
    gp = get_player(guild)
    bot_channel = vc.channel
    human_members = [m for m in bot_channel.members if not m.bot]
    if len(human_members) == 0:
        # Запускаємо таймер відключення
        if gp.disconnect_task and not gp.disconnect_task.done():
            gp.disconnect_task.cancel()
        gp.disconnect_task = asyncio.create_task(_auto_disconnect_timer(gp, vc))
    else:
        # Хтось є в каналі — скасовуємо таймер
        if gp.disconnect_task and not gp.disconnect_task.done():
            gp.disconnect_task.cancel()
            gp.disconnect_task = None


@bot.tree.command(name="join", description="Приєднатись у ваш голосовий канал")
async def join(interaction: discord.Interaction):
    gp = get_player(interaction.guild)
    try:
        vc = await gp.ensure_voice(interaction)
        await interaction.response.send_message(f"✅ У каналі: **{vc.channel.name}**", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ {e}", ephemeral=True)

@bot.tree.command(name="leave", description="Вийти з голосового каналу")
async def leave(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    gp = get_player(interaction.guild)
    if gp.disconnect_task and not gp.disconnect_task.done():
        gp.disconnect_task.cancel()
        gp.disconnect_task = None
    if vc:
        await vc.disconnect(force=True)
    await interaction.response.send_message("👋 Вийшов.", ephemeral=True)

@bot.tree.command(name="play", description="Додати трек/плейлист або пошукати на YouTube")
@app_commands.describe(query="URL або пошуковий запит")
async def play(interaction: discord.Interaction, query: str):
    await interaction.response.defer(thinking=True)
    gp = get_player(interaction.guild)
    try:
        vc = await gp.ensure_voice(interaction)
    except Exception as e:
        await interaction.followup.send(f"❌ {e}")
        return

    try:
        tracks = gp.yt.expand_input(query)
        if not tracks:
            await interaction.followup.send("Не знайшов нічого за запитом.")
            return

        russian_tracks = [t for t in tracks if is_russian_track(t)]

        await gp.add(tracks)
        added = f"Додав **{len(tracks)}** треків." if len(tracks) > 1 else f"Додав: **{tracks[0].title}**"
        await interaction.followup.send(added)

        if russian_tracks:
            await interaction.channel.send(
                "Фу, як ти це слухаєш?\nпіду вуха з хлоркою помию 🤢"
            )

        await gp.start_if_needed(vc, interaction.channel)
    except Exception as e:
        await interaction.followup.send(f"Помилка: {e}")

@bot.tree.command(name="queue", description="Показати чергу")
async def queue_cmd(interaction: discord.Interaction):
    gp = get_player(interaction.guild)
    qsize = gp.queue.qsize()
    msg = []
    if gp.current:
        msg.append(f"🎧 Зараз: **{gp.current.title}**")
    if qsize == 0:
        msg.append("Черга порожня.")
    else:
        # переглянемо, не виймаючи
        items: List[Track] = []
        for _ in range(qsize):
            t = await gp.queue.get()
            items.append(t)
        for t in items:
            await gp.queue.put(t)
        lst = "\n".join([f"{i+1}. {t.title}" for i, t in enumerate(items[:15])])
        msg.append(f"🧾 Черга ({qsize}):\n{lst}")
    await interaction.response.send_message("\n".join(msg), ephemeral=True)

@bot.tree.command(name="skip", description="Пропустити трек")
async def skip(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if not vc or not vc.is_playing():
        await interaction.response.send_message("Нічого не грає.", ephemeral=True)
        return
    vc.stop()
    await interaction.response.send_message("⏭️ Пропустив.", ephemeral=True)

@bot.tree.command(name="pause", description="Пауза")
async def pause(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if not vc or not vc.is_playing():
        await interaction.response.send_message("Нічого не грає.", ephemeral=True)
        return
    vc.pause()
    await interaction.response.send_message("⏸️ Пауза.", ephemeral=True)

@bot.tree.command(name="resume", description="Продовжити")
async def resume(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if not vc:
        await interaction.response.send_message("Не підключений.", ephemeral=True)
        return
    vc.resume()
    await interaction.response.send_message("▶️ Продовжив.", ephemeral=True)

@bot.tree.command(name="stop", description="Зупинити і очистити чергу")
async def stop(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    gp = get_player(interaction.guild)
    # очистити чергу
    try:
        while not gp.queue.empty():
            gp.queue.get_nowait()
            gp.queue.task_done()
    except Exception:
        pass
    if vc:
        vc.stop()
    await interaction.response.send_message("⏹️ Зупинено. Чергу очищено.", ephemeral=True)

@bot.tree.command(name="autoplay", description="Автопродовження рекомендованими треками YouTube")
@app_commands.describe(mode="on / off")
async def autoplay(interaction: discord.Interaction, mode: str):
    gp = get_player(interaction.guild)
    mode = mode.lower()
    if mode not in ("on", "off"):
        await interaction.response.send_message("Вкажіть: `on` або `off`.", ephemeral=True)
        return
    gp.autoplay = (mode == "on")
    status = "увімкнено ✅" if gp.autoplay else "вимкнено ❌"
    await interaction.response.send_message(f"🔁 Автопродовження: **{status}**", ephemeral=True)

@bot.tree.command(name="now", description="Що зараз грає")
async def now(interaction: discord.Interaction):
    gp = get_player(interaction.guild)
    if gp.current:
        await interaction.response.send_message(f"🎧 **{gp.current.title}**\n{gp.current.webpage_url}", ephemeral=True)
    else:
        await interaction.response.send_message("Зараз нічого не грає.", ephemeral=True)

@bot.tree.command(name="help", description="Список усіх команд бота")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎵 MusicByKico — Список команд",
        description="Усі доступні команди музичного бота:",
        color=0x1DB954,
    )
    commands_list = [
        ("/join", "Приєднатись до вашого голосового каналу"),
        ("/leave", "Вийти з голосового каналу"),
        ("/play <url або запит>", "Відтворити трек/плейлист або знайти на YouTube"),
        ("/queue", "Показати поточну чергу треків"),
        ("/skip", "Пропустити поточний трек"),
        ("/pause", "Поставити відтворення на паузу"),
        ("/resume", "Продовжити відтворення"),
        ("/stop", "Зупинити відтворення та очистити чергу"),
        ("/now", "Показати поточний трек"),
        ("/autoplay on/off", "Увімкнути або вимкнути автопродовження (рекомендації YouTube). Російськомовні треки пропускаються автоматично."),
        ("/help", "Показати цей список команд"),
    ]
    for cmd, desc in commands_list:
        embed.add_field(name=cmd, value=desc, inline=False)
    embed.set_footer(text="Слухай музику з радістю! 🎧")
    await interaction.response.send_message(embed=embed, ephemeral=True)


if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise SystemExit("Вкажіть DISCORD_TOKEN у .env")
    bot.run(token)
