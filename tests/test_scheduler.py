import unittest
from unittest.mock import Mock, patch

import requests

from main import scheduled_collect
from scheduler.jobs import collect_all


class SchedulerTests(unittest.IsolatedAsyncioTestCase):
    async def test_scheduled_collection_runs_off_the_event_loop(self):
        database = object()
        collectors = []
        with patch("main.collect_all", return_value=2) as collect_all:
            result = await scheduled_collect(database, collectors)

        self.assertEqual(result, 2)
        collect_all.assert_called_once_with(database, collectors)

    def test_collection_continues_after_one_source_fails(self):
        broken = Mock()
        broken.source = "Недоступный источник"
        broken.fetch.side_effect = requests.Timeout("timeout")
        working = Mock()
        working.source = "Рабочий источник"
        working.fetch.return_value = [
            {
                "title": "Новости рыбы",
                "url": "https://example.ru/news/1",
                "source": "Рабочий источник",
                "description": "",
            }
        ]
        database = Mock()
        database.insert_items.return_value = 1

        inserted = collect_all(database, [broken, working])

        self.assertEqual(inserted, 1)
        working.fetch.assert_called_once()
        database.insert_items.assert_called_once_with(working.fetch.return_value)


if __name__ == "__main__":
    unittest.main()
