# -*- coding: utf-8 -*-
"""SQLite persistence for fused CS item OHLCV used in analysis."""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd


def _default_db_path() -> Path:
    return Path(os.getenv("CS_ANALYSIS_DB", "data/cs_analysis.db"))


class CSAnalysisStore:
    """Store merged item daily OHLCV rows (API + crawler)."""

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
                CREATE TABLE IF NOT EXISTS item_daily_ohlcv (
                    good_id INTEGER NOT NULL,
                    item_name TEXT,
                    market_hash_name TEXT,
                    platform TEXT NOT NULL,
                    date TEXT NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume REAL NOT NULL,
                    amount REAL,
                    pct_chg REAL,
                    ohlc_source TEXT NOT NULL,
                    volume_source TEXT NOT NULL,
                    data_quality TEXT NOT NULL,
                    built_at TEXT NOT NULL,
                    PRIMARY KEY (good_id, platform, date)
                );
                """
            )
            conn.commit()

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def upsert_item_ohlcv_rows(self, rows: Iterable[dict]) -> int:
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
                    row.get("open"),
                    row.get("high"),
                    row.get("low"),
                    row.get("close"),
                    float(row.get("volume") or 0),
                    row.get("amount"),
                    row.get("pct_chg"),
                    str(row.get("ohlc_source") or "unknown"),
                    str(row.get("volume_source") or "unknown"),
                    str(row.get("data_quality") or "degraded"),
                    stamp,
                )
            )
        if not payload:
            return 0
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT INTO item_daily_ohlcv (
                    good_id, item_name, market_hash_name, platform, date,
                    open, high, low, close, volume, amount, pct_chg,
                    ohlc_source, volume_source, data_quality, built_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(good_id, platform, date) DO UPDATE SET
                    item_name=excluded.item_name,
                    market_hash_name=excluded.market_hash_name,
                    open=excluded.open,
                    high=excluded.high,
                    low=excluded.low,
                    close=excluded.close,
                    volume=excluded.volume,
                    amount=excluded.amount,
                    pct_chg=excluded.pct_chg,
                    ohlc_source=excluded.ohlc_source,
                    volume_source=excluded.volume_source,
                    data_quality=excluded.data_quality,
                    built_at=excluded.built_at
                """,
                payload,
            )
            conn.commit()
        return len(payload)

    def read_item_ohlcv(
        self,
        *,
        good_id: int,
        platform: Optional[str] = None,
    ) -> pd.DataFrame:
        query = "SELECT * FROM item_daily_ohlcv WHERE good_id = ?"
        params: list = [int(good_id)]
        if platform:
            query += " AND LOWER(platform) = LOWER(?)"
            params.append(str(platform))
        query += " ORDER BY date"
        with self._connect() as conn:
            return pd.read_sql_query(query, conn, params=params)
