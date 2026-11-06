"""Start the RSS collectors, scheduler, and Telegram bot."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram.ext import Application

from bot.telegram_bot import configure_bot
from collectors import RssCollector
from collectors.base import Collector
from config import Settings
from database.db import Database
from scheduler.jobs import collect_all, send_digest

logger = logging.getLogger(__name__)


def create_collectors(settings: Settings) -> list[Collector]:
    return [
        RssCollector(
            source="Fishnews",
            feed_url=settings.fishnews_rss_url,
            timeout=settings.request_timeout_seconds,
        ),
        RssCollector(
            source="Fishretail",
            feed_url=settings.fishretail_rss_url,
            timeout=settings.request_timeout_seconds,
        ),
    ]


async def scheduled_collect(
    database: Database, collectors: Sequence[Collector]
) -> int:
    return await asyncio.to_thread(collect_all, database, collectors)


async def run_service(settings: Settings) -> None:
    database = Database(settings.database_path)
    collectors = create_collectors(settings)
    application = Application.builder().token(settings.telegram_bot_token).build()
    configure_bot(application, settings, database)
    scheduler = AsyncIOScheduler(timezone=settings.timezone)
    scheduler.add_job(
        scheduled_collect,
        trigger="interval",
        minutes=settings.collect_interval_minutes,
        args=[database, collectors],
        id="collect_news",
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        send_digest,
        trigger="cron",
        hour=settings.digest_hour,
        minute=settings.digest_minute,
        timezone=settings.timezone,
        args=[application.bot, settings.telegram_chat_id, database],
        id="daily_digest",
        max_instances=1,
        coalesce=True,
    )

    await scheduled_collect(database, collectors)
    await application.initialize()
    await application.start()
    if application.updater is None:
        raise RuntimeError("Telegram updater не инициализирован.")
    await application.updater.start_polling()
    scheduler.start()
    logger.info(
        "Агрегатор запущен: сбор каждые %d мин., дайджест ежедневно в %02d:%02d (%s)",
        settings.collect_interval_minutes,
        settings.digest_hour,
        settings.digest_minute,
        settings.timezone,
    )
    try:
        await asyncio.Event().wait()
    finally:
        scheduler.shutdown(wait=False)
        await application.updater.stop()
        await application.stop()
        await application.shutdown()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    try:
        settings = Settings.from_env()
    except ValueError as error:
        raise SystemExit(f"Ошибка конфигурации: {error}") from error
    asyncio.run(run_service(settings))


if __name__ == "__main__":
    main()
