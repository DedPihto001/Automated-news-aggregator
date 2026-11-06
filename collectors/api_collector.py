"""Generic collector for public JSON APIs."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import requests

from collectors.base import Collector, NewsRecord, normalize_record


class ApiCollector(Collector):
    def __init__(
        self,
        source: str,
        endpoint: str,
        *,
        items_key: str = "items",
        timeout: int = 20,
    ) -> None:
        super().__init__(source, timeout)
        self.endpoint = endpoint
        self.items_key = items_key

    def fetch(self) -> list[NewsRecord]:
        response = requests.get(
            self.endpoint,
            timeout=self.timeout,
            headers={"Accept": "application/json", "User-Agent": "RussianSeafoodNewsAggregator/1.0"},
        )
        response.raise_for_status()
        payload: Any = response.json()
        items: Any = payload
        for key in filter(None, self.items_key.split(".")):
            if not isinstance(items, Mapping) or key not in items:
                raise ValueError(f"В ответе API отсутствует поле {key!r}.")
            items = items[key]
        if not isinstance(items, list):
            raise ValueError("Ожидался список материалов в ответе API.")

        records: list[NewsRecord] = []
        for item in items:
            if not isinstance(item, Mapping):
                continue
            record = normalize_record(
                title=str(item.get("title") or ""),
                url=str(item.get("url") or ""),
                source=self.source,
                description=str(item.get("description") or ""),
                base_url=self.endpoint,
            )
            if record is not None:
                records.append(record)
        return records
