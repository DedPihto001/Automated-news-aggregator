"""SQLite persistence for collected news."""

from database.db import Database
from database.models import NewsItem

__all__ = ["Database", "NewsItem"]
