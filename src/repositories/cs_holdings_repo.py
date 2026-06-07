# -*- coding: utf-8 -*-
"""CS holdings persistence."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import delete, func, or_, select

from src.storage import CSHolding, DatabaseManager


class CSHoldingsRepository:
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager.get_instance()

    def _apply_filters(self, query, *, platform: Optional[str] = None):
        if platform:
            query = query.where(CSHolding.platform == platform.lower())
        return query

    def list_all(self, *, platform: Optional[str] = None) -> List[CSHolding]:
        with self.db.get_session() as session:
            query = select(CSHolding).order_by(CSHolding.updated_at.desc(), CSHolding.id.desc())
            query = self._apply_filters(query, platform=platform)
            rows = session.execute(query).scalars().all()
            return list(rows)

    def list_paginated(
        self,
        *,
        page: int = 1,
        page_size: int = 50,
        platform: Optional[str] = None,
        sort: str = "updated_at",
    ) -> Tuple[List[CSHolding], int]:
        page = max(1, int(page))
        page_size = max(1, min(int(page_size), 200))
        with self.db.get_session() as session:
            count_query = select(func.count(CSHolding.id))
            count_query = self._apply_filters(count_query, platform=platform)
            total = session.execute(count_query).scalar() or 0
            order_col = CSHolding.updated_at
            if sort == "market_price":
                order_col = CSHolding.market_price
            elif sort == "purchase_price":
                order_col = CSHolding.purchase_price
            query = select(CSHolding)
            query = self._apply_filters(query, platform=platform)
            query = query.order_by(order_col.desc(), CSHolding.id.desc())
            query = query.offset((page - 1) * page_size).limit(page_size)
            rows = session.execute(query).scalars().all()
            return list(rows), int(total)

    def find_by_dedup_keys(self, dedup_keys: List[str]) -> List[CSHolding]:
        keys = [k for k in dedup_keys if k]
        if not keys:
            return []
        with self.db.get_session() as session:
            rows = session.execute(
                select(CSHolding).where(CSHolding.dedup_key.in_(keys))
            ).scalars().all()
            return list(rows)

    def delete_by_batch_id(self, batch_id: str) -> int:
        with self.db.get_session() as session:
            result = session.execute(
                delete(CSHolding).where(CSHolding.import_batch_id == batch_id)
            )
            session.commit()
            return int(result.rowcount or 0)

    def list_without_good_id(self) -> List[CSHolding]:
        with self.db.get_session() as session:
            rows = session.execute(
                select(CSHolding)
                .where(or_(CSHolding.good_id.is_(None), CSHolding.good_id == 0))
                .order_by(CSHolding.updated_at.desc(), CSHolding.id.desc())
            ).scalars().all()
            return list(rows)

    def get(self, holding_id: int) -> Optional[CSHolding]:
        with self.db.get_session() as session:
            return session.get(CSHolding, holding_id)

    def create(self, payload: Dict[str, Any]) -> CSHolding:
        with self.db.get_session() as session:
            row = CSHolding(**payload)
            session.add(row)
            session.commit()
            session.refresh(row)
            return row

    def bulk_create(self, payloads: List[Dict[str, Any]]) -> List[CSHolding]:
        with self.db.get_session() as session:
            rows = [CSHolding(**payload) for payload in payloads]
            session.add_all(rows)
            session.commit()
            for row in rows:
                session.refresh(row)
            return rows

    def update(self, holding_id: int, payload: Dict[str, Any]) -> Optional[CSHolding]:
        with self.db.get_session() as session:
            row = session.get(CSHolding, holding_id)
            if row is None:
                return None
            for key, value in payload.items():
                if hasattr(row, key):
                    setattr(row, key, value)
            session.commit()
            session.refresh(row)
            return row

    def delete(self, holding_id: int) -> bool:
        with self.db.get_session() as session:
            row = session.get(CSHolding, holding_id)
            if row is None:
                return False
            session.delete(row)
            session.commit()
            return True
