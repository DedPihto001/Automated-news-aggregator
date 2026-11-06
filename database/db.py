"""SQLite schema and operations for news items and digest delivery state."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Iterable

from collectors.base import NewsRecord
from database.models import NewsItem


class Database:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def initialize(self) -> None:
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    source TEXT NOT NULL,
                    description TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_items_url ON items(url)"
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS delivered_items (
                    item_id INTEGER PRIMARY KEY REFERENCES items(id),
                    delivered_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def insert_items(self, items: Iterable[NewsRecord]) -> int:
        inserted = 0
        with closing(sqlite3.connect(self.path)) as connection, connection:
            for item in items:
                cursor = connection.execute(
                    """
                    INSERT OR IGNORE INTO items (title, url, source, description)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        item["title"],
                        item["url"],
                        item["source"],
                        item["description"],
                    ),
                )
                inserted += cursor.rowcount
        return inserted

    def get_undelivered_items(self) -> list[NewsItem]:
        with closing(sqlite3.connect(self.path)) as connection:
            rows = connection.execute(
                """
                SELECT i.id, i.title, i.url, i.source, i.description, i.created_at
                FROM items AS i
                LEFT JOIN delivered_items AS d ON d.item_id = i.id
                WHERE d.item_id IS NULL
                ORDER BY i.source, i.created_at DESC, i.id DESC
                """
            ).fetchall()
        return [NewsItem(*row) for row in rows]

    def mark_delivered(self, item_ids: Iterable[int]) -> None:
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.executemany(
                "INSERT OR IGNORE INTO delivered_items (item_id) VALUES (?)",
                ((item_id,) for item_id in item_ids),
            )

    def list_items(self, limit: int = 20) -> list[NewsItem]:
        if limit < 1:
            raise ValueError("Лимит должен быть положительным числом.")
        with closing(sqlite3.connect(self.path)) as connection:
            rows = connection.execute(
                """
                SELECT id, title, url, source, description, created_at
                FROM items
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [NewsItem(*row) for row in rows]
