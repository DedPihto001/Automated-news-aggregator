"""Collection and Telegram digest job helpers."""

from __future__ import annotations

import logging
from collections.abc import Sequence

import requests
from telegram import Bot
from telegram.error import TelegramError

from collectors.base import Collector
from database.db import Database
from database.models import NewsItem

logger = logging.getLogger(__name__)
TELEGRAM_MESSAGE_LIMIT = 4000


def collect_all(database: Database, collectors: Sequence[Collector]) -> int:
    total_inserted = 0
    for collector in collectors:
        try:
            records = collector.fetch()
            inserted = database.insert_items(records)
        except (requests.RequestException, ValueError) as error:
            logger.exception("Не удалось собрать новости из %s: %s", collector.source, error)
            continue
        total_inserted += inserted
        logger.info(
            "Источник %s: получено %d, добавлено %d новых материалов",
            collector.source,
            len(records),
            inserted,
        )
    logger.info("Сбор завершён: добавлено %d новых материалов", total_inserted)
    return total_inserted


def format_digest(items: Sequence[NewsItem]) -> str:
    if not items:
        return "Новых материалов пока нет."

    lines = ["📰 Дайджест новостей рыбной отрасли"]
    current_source = ""
    for item in items:
        if item.source != current_source:
            current_source = item.source
            lines.extend(("", f"Источник: {current_source}"))
        description = item.description.strip()
        if len(description) > 250:
            description = description[:247].rstrip() + "..."
        lines.append(f"• {item.title}\n{item.url}")
        if description:
            lines.append(description)
    return "\n".join(lines)


def split_digest(text: str, limit: int = TELEGRAM_MESSAGE_LIMIT) -> list[str]:
    if len(text) <= limit:
        return [text]
    chunks: list[str] = []
    current = ""
    for block in text.split("\n\n"):
        if len(block) > limit:
            raise ValueError("Один блок дайджеста превышает лимит Telegram.")
        candidate = f"{current}\n\n{block}" if current else block
        if len(candidate) > limit:
            chunks.append(current)
            current = block
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


async def send_digest(bot: Bot, chat_id: str, database: Database) -> int:
    items = database.get_undelivered_items()
    text = format_digest(items)
    try:
        for chunk in split_digest(text):
            await bot.send_message(chat_id=chat_id, text=chunk, disable_web_page_preview=True)
    except TelegramError:
        logger.exception("Не удалось отправить дайджест в Telegram.")
        raise
    if items:
        database.mark_delivered([item.id for item in items])
    logger.info("Дайджест отправлен; материалов: %d", len(items))
    return len(items)
