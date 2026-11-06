import unittest
from unittest.mock import Mock, patch

from collectors.api_collector import ApiCollector
from collectors.base import clean_html, normalize_record
from collectors.rss_collector import RssCollector


class CollectorTests(unittest.TestCase):
    def test_normalize_record_cleans_html_and_resolves_relative_urls(self):
        record = normalize_record(
            title="  Новость&nbsp; о рыбе ",
            url="/news/1",
            source="  Fish News  ",
            description="<p>Цена <b>рыбы</b></p>",
            base_url="https://example.ru/rss",
        )

        self.assertEqual(
            record,
            {
                "title": "Новость о рыбе",
                "url": "https://example.ru/news/1",
                "source": "Fish News",
                "description": "Цена рыбы",
            },
        )

    def test_clean_html_decodes_entities_and_removes_markup(self):
        self.assertEqual(clean_html(" <p>Креветки &amp; рыба</p> "), "Креветки & рыба")

    @patch("collectors.rss_collector.feedparser.parse")
    @patch("collectors.rss_collector.requests.get")
    def test_rss_collector_fetches_and_normalizes_feed(self, get, parse):
        get.return_value.content = b"<rss/>"
        get.return_value.raise_for_status.return_value = None
        parse.return_value.bozo = False
        parse.return_value.entries = [
            {
                "title": "Лосось",
                "link": "https://fish.example/news/1",
                "summary": "<p>Новости рыбы</p>",
            }
        ]

        items = RssCollector("Feed", "https://fish.example/rss").fetch()

        self.assertEqual(items[0]["description"], "Новости рыбы")
        get.assert_called_once()

    @patch("collectors.api_collector.requests.get")
    def test_api_collector_reads_public_json_items(self, get):
        response = Mock()
        response.json.return_value = {
            "data": [
                {"title": "Краб", "url": "/news/2", "description": "<b>Цена</b>"}
            ]
        }
        get.return_value = response

        items = ApiCollector(
            "Public API", "https://example.ru/api/news", items_key="data"
        ).fetch()

        self.assertEqual(items[0]["url"], "https://example.ru/news/2")
        self.assertEqual(items[0]["description"], "Цена")


if __name__ == "__main__":
    unittest.main()
