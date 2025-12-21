"""In-memory storage layer with optional sqlite cache."""
from __future__ import annotations

import sqlite3
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd

from .models import ListingRecord


class InMemoryStorage:
    """Keep scraped items in a pandas DataFrame and track duplicates."""

    def __init__(self) -> None:
        self._records: list[ListingRecord] = []
        self._seen: set[str] = set()

    @property
    def dataframe(self) -> pd.DataFrame:
        if not self._records:
            return pd.DataFrame(columns=ListingRecord.headers())
        return pd.DataFrame([rec.as_row() for rec in self._records])

    def add_record(self, record: ListingRecord) -> bool:
        key = record.ilan_no or record.link
        if key in self._seen:
            return False
        self._seen.add(key)
        self._records.append(record)
        return True

    def reset(self) -> None:
        self._records.clear()
        self._seen.clear()

    def extend(self, records: Iterable[ListingRecord]) -> int:
        count = 0
        for rec in records:
            if self.add_record(rec):
                count += 1
        return count


class SqliteCache:
    """Optional lightweight cache for listing metadata."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS listings (
                    ilan_no TEXT PRIMARY KEY,
                    link TEXT,
                    updated_at TEXT,
                    payload TEXT
                )
                """
            )

    def upsert(self, record: ListingRecord, updated_at: str) -> None:
        payload = asdict(record)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO listings (ilan_no, link, updated_at, payload)
                VALUES (?, ?, ?, json(?))
                ON CONFLICT(ilan_no) DO UPDATE SET
                    link=excluded.link,
                    updated_at=excluded.updated_at,
                    payload=excluded.payload
                """,
                (record.ilan_no, record.link, updated_at, payload),
            )

    def exists(self, ilan_no: Optional[str]) -> bool:
        if not ilan_no:
            return False
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT 1 FROM listings WHERE ilan_no=?", (ilan_no,))
            return cursor.fetchone() is not None
