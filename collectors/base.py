"""Shared collector interface and content normalization."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from html import unescape
from html.parser import HTMLParser
from typing import TypedDict
from urllib.parse import urljoin, urlsplit


class NewsRecord(TypedDict):
    title: str
    url: str
    source: str
    description: str


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def clean_html(value: str) -> str:
    parser = _TextExtractor()
    parser.feed(unescape(value))
    parser.close()
    return re.sub(r"\s+", " ", " ".join(parser.parts)).strip()


def normalize_record(
    *,
    title: str,
    url: str,
    source: str,
    description: str = "",
    base_url: str = "",
) -> NewsRecord | None:
    normalized_title = re.sub(r"\s+", " ", unescape(title)).strip()
    raw_url = unescape(url.strip())
    if not raw_url:
        return None
    normalized_url = urljoin(base_url, raw_url).strip()
    normalized_source = re.sub(r"\s+", " ", source).strip()
    parsed_url = urlsplit(normalized_url)
    if (
        not normalized_title
        or not normalized_source
        or parsed_url.scheme not in {"http", "https"}
        or not parsed_url.netloc
    ):
        return None
    return {
        "title": normalized_title,
        "url": normalized_url,
        "source": normalized_source,
        "description": clean_html(description),
    }


class Collector(ABC):
    """Fetch normalized news items from a single public source."""

    def __init__(self, source: str, timeout: int = 20) -> None:
        self.source = source
        self.timeout = timeout

    @abstractmethod
    def fetch(self) -> list[NewsRecord]:
        """Return normalized records from this source."""
