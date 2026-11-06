import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from database.db import Database


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = Database(Path(self.temp_dir.name) / "news.db")

    def tearDown(self):
        self.temp_dir.cleanup()

    @staticmethod
    def item(url, title="Новость"):
        return {
            "title": title,
            "url": url,
            "source": "Источник",
            "description": "Описание",
        }

    def test_items_schema_and_unique_url_deduplication(self):
        with closing(sqlite3.connect(self.database.path)) as connection:
            columns = connection.execute("PRAGMA table_info(items)").fetchall()
            names = [column[1] for column in columns]
        self.assertEqual(
            names, ["id", "title", "url", "source", "description", "created_at"]
        )

        inserted = self.database.insert_items(
            [self.item("https://example.ru/news/1"), self.item("https://example.ru/news/1")]
        )

        self.assertEqual(inserted, 1)
        self.assertEqual(len(self.database.list_items()), 1)

    def test_delivery_state_only_returns_new_items(self):
        self.database.insert_items([self.item("https://example.ru/news/1")])
        item = self.database.get_undelivered_items()[0]

        self.database.mark_delivered([item.id])

        self.assertEqual(self.database.get_undelivered_items(), [])


if __name__ == "__main__":
    unittest.main()
