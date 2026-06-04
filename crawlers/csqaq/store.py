# -*- coding: utf-8 -*-
"""SQLite persistence for CSQAQ volume crawl results."""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd


def _default_db_path() -> Path:
    return Path(os.getenv("CSQAQ_CRAWL_DB", "data/cs_crawl_volume.db"))


class VolumeCrawlStore:
    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = db_path or _default_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS index_daily_volume (
                    sub_index_id TEXT NOT NULL,
                    sub_index_name TEXT,
                    date TEXT NOT NULL,
                    volume REAL NOT NULL,
                    close REAL,
                    open REAL,
                    high REAL,
                    low REAL,
                    volume_source TEXT NOT NULL,
                    crawled_at TEXT NOT NULL,
                    PRIMARY KEY (sub_index_id, date, volume_source)
                );

                CREATE TABLE IF NOT EXISTS item_daily_volume (
                    good_id INTEGER NOT NULL,
                    item_name TEXT,
                    market_hash_name TEXT,
                    platform TEXT,
                    date TEXT NOT NULL,
                    volume REAL NOT NULL,
                    close REAL,
                    open REAL,
                    high REAL,
                    low REAL,
                    volume_source TEXT NOT NULL,
                    crawled_at TEXT NOT NULL,
                    PRIMARY KEY (good_id, platform, date, volume_source)
                );
                """
            )
            self._ensure_item_ohlc_columns(conn)
            conn.commit()

    def _ensure_item_ohlc_columns(self, conn: sqlite3.Connection) -> None:
        existing = {row[1] for row in conn.execute("PRAGMA table_info(item_daily_volume)")}
        for column, col_type in (("open", "REAL"), ("high", "REAL"), ("low", "REAL")):
            if column not in existing:
                conn.execute(f"ALTER TABLE item_daily_volume ADD COLUMN {column} {col_type}")

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def upsert_index_rows(self, rows: Iterable[dict]) -> int:
        stamp = self._now_iso()
        payload = []
        for row in rows:
            payload.append(
                (
                    str(row["sub_index_id"]),
                    row.get("sub_index_name"),
                    str(row["date"]),
                    float(row.get("volume") or 0),
                    row.get("close"),
                    row.get("open"),
                    row.get("high"),
                    row.get("low"),
                    str(row.get("volume_source") or "unknown"),
                    stamp,
                )
            )
        if not payload:
            return 0
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT INTO index_daily_volume (
                    sub_index_id, sub_index_name, date, volume, close, open, high, low,
                    volume_source, crawled_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(sub_index_id, date, volume_source) DO UPDATE SET
                    sub_index_name=excluded.sub_index_name,
                    volume=excluded.volume,
                    close=excluded.close,
                    open=excluded.open,
                    high=excluded.high,
                    low=excluded.low,
                    crawled_at=excluded.crawled_at
                """,
                payload,
            )
            conn.commit()
        return len(payload)

    def upsert_item_rows(self, rows: Iterable[dict]) -> int:
        stamp = self._now_iso()
        payload = []
        for row in rows:
            payload.append(
                (
                    int(row["good_id"]),
                    row.get("item_name"),
                    row.get("market_hash_name"),
                    str(row.get("platform") or "unknown"),
                    str(row["date"]),
                    float(row.get("volume") or 0),
                    row.get("close"),
                    row.get("open"),
                    row.get("high"),
                    row.get("low"),
                    str(row.get("volume_source") or "unknown"),
                    stamp,
                )
            )
        if not payload:
            return 0
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT INTO item_daily_volume (
                    good_id, item_name, market_hash_name, platform, date, volume, close,
                    open, high, low, volume_source, crawled_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(good_id, platform, date, volume_source) DO UPDATE SET
                    item_name=excluded.item_name,
                    market_hash_name=excluded.market_hash_name,
                    volume=excluded.volume,
                    close=excluded.close,
                    open=excluded.open,
                    high=excluded.high,
                    low=excluded.low,
                    crawled_at=excluded.crawled_at
                """,
                payload,
            )
            conn.commit()
        return len(payload)

    def read_index_frame(self, *, sub_index_id: Optional[str] = None) -> pd.DataFrame:
        query = "SELECT * FROM index_daily_volume"
        params: tuple = ()
        if sub_index_id:
            query += " WHERE sub_index_id = ?"
            params = (str(sub_index_id),)
        query += " ORDER BY date"
        with self._connect() as conn:
            return pd.read_sql_query(query, conn, params=params)

    def read_item_frame(self, *, good_id: Optional[int] = None) -> pd.DataFrame:
        query = "SELECT * FROM item_daily_volume"
        params: tuple = ()
        if good_id is not None:
            query += " WHERE good_id = ?"
            params = (int(good_id),)
        query += " ORDER BY good_id, date"
        with self._connect() as conn:
            return pd.read_sql_query(query, conn, params=params)

    def read_item_kline(
        self,
        *,
        good_id: int,
        platform: Optional[str] = None,
        volume_source: str = "kline_chart_all_v",
    ) -> pd.DataFrame:
        """Return browser K-line rows for one item (optionally filtered by platform)."""
        query = "SELECT * FROM item_daily_volume WHERE good_id = ? AND volume_source = ?"
        params: list = [int(good_id), str(volume_source)]
        if platform:
            query += " AND LOWER(platform) = LOWER(?)"
            params.append(str(platform))
        query += " ORDER BY date"
        with self._connect() as conn:
            return pd.read_sql_query(query, conn, params=params)
