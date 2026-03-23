from __future__ import annotations

import asyncio

from src.bot.client import MusicBot
from src.core.logging import configure_logging


async def main() -> None:
    configure_logging()
    bot = MusicBot()
    async with bot:
        await bot.start(bot.settings.discord_token)


if __name__ == "__main__":
    asyncio.run(main())