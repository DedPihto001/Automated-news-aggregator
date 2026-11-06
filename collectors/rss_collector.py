"""RSS/Atom feed collector."""

from __future__ import annotations

import feedparser
import requests

from collectors.base import Collector, NewsRecord, normalize_record


class RssCollector(Collector):
    def __init__(
        self, source: str, feed_url: str, timeout: int = 20
    ) -> None:
        super().__init__(source, timeout)
        self.feed_url = feed_url

    def fetch(self) -> list[NewsRecord]:
        response = requests.get(
            self.feed_url,
            timeout=self.timeout,
            headers={"User-Agent": "RussianSeafoodNewsAggregator/1.0"},
        )
        response.raise_for_status()
        feed = feedparser.parse(response.content)
        if feed.bozo and not feed.entries:
            raise ValueError(f"Некорректная RSS-лента: {feed.bozo_exception}")

        records: list[NewsRecord] = []
        for entry in feed.entries:
            summary = entry.get("summary", "")
            content = entry.get("content", [])
            if content and isinstance(content, list):
                summary = content[0].get("value", summary)
            record = normalize_record(
                title=entry.get("title", ""),
                url=entry.get("link", ""),
                source=self.source,
                description=summary,
                base_url=self.feed_url,
            )
            if record is not None:
                records.append(record)
        return records
