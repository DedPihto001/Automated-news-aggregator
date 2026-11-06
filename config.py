"""Application configuration loaded from environment or a local .env file."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    telegram_chat_id: str
    fishnews_rss_url: str
    fishretail_rss_url: str
    database_path: Path
    collect_interval_minutes: int
    digest_hour: int
    digest_minute: int
    timezone: str
    request_timeout_seconds: int

    @classmethod
    def from_env(cls) -> Settings:
        load_dotenv()
        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
        if not token or token == "your_token_here":
            raise ValueError("Укажите TELEGRAM_BOT_TOKEN в файле .env.")
        if not chat_id or chat_id == "your_chat_id_here":
            raise ValueError("Укажите TELEGRAM_CHAT_ID в файле .env.")

        interval = int(os.getenv("COLLECT_INTERVAL_MINUTES", "60"))
        digest_hour = int(os.getenv("DIGEST_HOUR", "9"))
        digest_minute = int(os.getenv("DIGEST_MINUTE", "0"))
        timeout = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "20"))
        if interval < 1:
            raise ValueError("COLLECT_INTERVAL_MINUTES должен быть не меньше 1.")
        if not 0 <= digest_hour <= 23:
            raise ValueError("DIGEST_HOUR должен быть от 0 до 23.")
        if not 0 <= digest_minute <= 59:
            raise ValueError("DIGEST_MINUTE должен быть от 0 до 59.")
        if timeout < 1:
            raise ValueError("REQUEST_TIMEOUT_SECONDS должен быть не меньше 1.")
        timezone = os.getenv("TIMEZONE", "Europe/Moscow").strip()
        try:
            ZoneInfo(timezone)
        except ZoneInfoNotFoundError as error:
            raise ValueError(f"Неизвестный часовой пояс TIMEZONE: {timezone}.") from error

        return cls(
            telegram_bot_token=token,
            telegram_chat_id=chat_id,
            fishnews_rss_url=os.getenv(
                "FISHNEWS_RSS_URL", "https://fishnews.ru/rss.xml"
            ).strip(),
            fishretail_rss_url=os.getenv(
                "FISHRETAIL_RSS_URL", "https://fishretail.ru/news/rss"
            ).strip(),
            database_path=Path(os.getenv("DATABASE_PATH", "data/news.db")),
            collect_interval_minutes=interval,
            digest_hour=digest_hour,
            digest_minute=digest_minute,
            timezone=timezone,
            request_timeout_seconds=timeout,
        )
