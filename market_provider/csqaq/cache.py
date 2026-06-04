# -*- coding: utf-8 -*-
"""SQLite cache hooks for CSQAQ API responses (Phase 1 stub implementation)."""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional


def _default_db_path() -> Path:
    raw = os.getenv("CSQAQ_CACHE_DB", "data/cs_csqaq_cache.db")
    return Path(raw)


class CSQAQCacheStore:
    """
    Minimal SQLite cache for CSQAQ HTTP payloads.

    Phase 1 exposes get/put hooks; callers may disable caching by passing
    ``cache=None`` to :class:`CSQAQClient`.
    """

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
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS csqaq_cache (
                    cache_key TEXT PRIMARY KEY,
                    payload BLOB NOT NULL,
                    expires_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_csqaq_cache_expires
                ON csqaq_cache (expires_at)
                """
            )
            conn.commit()

    def get(self, cache_key: str) -> Optional[bytes]:
        """Return cached payload bytes when present and not expired."""
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT payload FROM csqaq_cache
                WHERE cache_key = ? AND expires_at > ?
                """,
                (cache_key, now),
            ).fetchone()
        if row is None:
            return None
        return bytes(row["payload"])

    def put(self, cache_key: str, payload: bytes, ttl_seconds: int = 3600) -> None:
        """Store payload with a TTL."""
        now = datetime.now(timezone.utc)
        expires_at = (now + timedelta(seconds=max(1, ttl_seconds))).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO csqaq_cache (cache_key, payload, expires_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                    payload = excluded.payload,
                    expires_at = excluded.expires_at,
                    updated_at = excluded.updated_at
                """,
                (cache_key, payload, expires_at, now.isoformat()),
            )
            conn.commit()

    def invalidate(self, cache_key: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM csqaq_cache WHERE cache_key = ?", (cache_key,))
            conn.commit()

    def purge_expired(self) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM csqaq_cache WHERE expires_at <= ?",
                (now,),
            )
            conn.commit()
            return int(cursor.rowcount)
