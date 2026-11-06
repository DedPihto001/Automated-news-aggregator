"""Telegram commands for the private news digest bot."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from config import Settings
from database.db import Database
from scheduler.jobs import send_digest

logger = logging.getLogger(__name__)


async def digest_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    settings: Settings = context.application.bot_data["settings"]
    if update.effective_chat is None or str(update.effective_chat.id) != settings.telegram_chat_id:
        logger.warning("Команда /digest получена из неразрешенного чата.")
        return
    message = update.effective_message
    if message is None:
        return
    database: Database = context.application.bot_data["database"]
    await send_digest(context.bot, settings.telegram_chat_id, database)


async def start_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    settings: Settings = context.application.bot_data["settings"]
    message = update.effective_message
    if (
        message is not None
        and update.effective_chat is not None
        and str(update.effective_chat.id) == settings.telegram_chat_id
    ):
        await message.reply_text(
            "Бот новостного агрегатора запущен. Используйте /digest, чтобы получить новые материалы."
        )


def configure_bot(application: Application, settings: Settings, database: Database) -> None:
    application.bot_data["settings"] = settings
    application.bot_data["database"] = database
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("digest", digest_command))
