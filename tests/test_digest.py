import unittest
from unittest.mock import AsyncMock, MagicMock

from database.models import NewsItem
from scheduler.jobs import format_digest, send_digest, split_digest


class DigestTests(unittest.IsolatedAsyncioTestCase):
    def item(self, item_id, title, source="Fishnews"):
        return NewsItem(
            id=item_id,
            title=title,
            url=f"https://example.ru/news/{item_id}",
            source=source,
            description="Описание",
            created_at="2026-11-06 09:00:00",
        )

    def test_format_digest_groups_by_source(self):
        text = format_digest([self.item(1, "Лосось"), self.item(2, "Краб", "Fishretail")])

        self.assertIn("Источник: Fishnews", text)
        self.assertIn("Источник: Fishretail", text)
        self.assertIn("https://example.ru/news/1", text)

    def test_split_digest_respects_telegram_limit(self):
        chunks = split_digest("Первая новость\n\n" + ("x" * 50) + "\n\nВторая новость", 60)

        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk) <= 60 for chunk in chunks))

    async def test_send_digest_marks_items_only_after_success(self):
        bot = AsyncMock()
        database = MagicMock()
        database.get_undelivered_items.return_value = [self.item(1, "Лосось")]

        sent = await send_digest(bot, "123", database)

        self.assertEqual(sent, 1)
        database.mark_delivered.assert_called_once_with([1])

    async def test_send_digest_keeps_items_undelivered_when_send_fails(self):
        bot = AsyncMock()
        bot.send_message.side_effect = RuntimeError("network error")
        database = MagicMock()
        database.get_undelivered_items.return_value = [self.item(1, "Лосось")]

        with self.assertRaises(RuntimeError):
            await send_digest(bot, "123", database)

        database.mark_delivered.assert_not_called()


if __name__ == "__main__":
    unittest.main()
