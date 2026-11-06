"""Database record models."""

from dataclasses import dataclass


@dataclass(frozen=True)
class NewsItem:
    id: int
    title: str
    url: str
    source: str
    description: str
    created_at: str
