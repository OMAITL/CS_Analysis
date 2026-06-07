# -*- coding: utf-8 -*-
"""CS holdings import batch persistence."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select

from src.storage import CSHoldingImportBatch, DatabaseManager


class CSHoldingImportRepository:
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager.get_instance()

    def create_batch(self, payload: Dict[str, Any]) -> CSHoldingImportBatch:
        with self.db.get_session() as session:
            row = CSHoldingImportBatch(**payload)
            session.add(row)
            session.commit()
            session.refresh(row)
            return row

    def get_batch(self, batch_id: str) -> Optional[CSHoldingImportBatch]:
        with self.db.get_session() as session:
            return session.get(CSHoldingImportBatch, batch_id)

    def update_batch(self, batch_id: str, payload: Dict[str, Any]) -> Optional[CSHoldingImportBatch]:
        with self.db.get_session() as session:
            row = session.get(CSHoldingImportBatch, batch_id)
            if row is None:
                return None
            for key, value in payload.items():
                if hasattr(row, key):
                    setattr(row, key, value)
            session.commit()
            session.refresh(row)
            return row

    def list_batches(self, *, limit: int = 20) -> List[CSHoldingImportBatch]:
        with self.db.get_session() as session:
            rows = session.execute(
                select(CSHoldingImportBatch)
                .order_by(CSHoldingImportBatch.created_at.desc())
                .limit(max(1, int(limit)))
            ).scalars().all()
            return list(rows)

    def mark_committed(self, batch_id: str, *, item_count: int) -> Optional[CSHoldingImportBatch]:
        return self.update_batch(
            batch_id,
            {
                "status": "committed",
                "item_count": item_count,
                "committed_at": datetime.now(),
            },
        )

    def mark_rolled_back(self, batch_id: str) -> Optional[CSHoldingImportBatch]:
        return self.update_batch(batch_id, {"status": "rolled_back"})
