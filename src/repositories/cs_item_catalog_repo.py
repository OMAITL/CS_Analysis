# -*- coding: utf-8 -*-
"""CS item catalog persistence (CSQAQ get_page_list mirror)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from src.storage import CSItemCatalog, CSItemCatalogState, DatabaseManager


def _normalize_search_blob(name: str, market_hash_name: str) -> str:
    parts = [name or '', market_hash_name or '']
    return ' '.join(part.strip().lower() for part in parts if part and part.strip())


class CSItemCatalogRepository:
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager.get_instance()

    def get_by_good_id(self, good_id: int) -> Optional[CSItemCatalog]:
        with self.db.get_session() as session:
            return session.get(CSItemCatalog, int(good_id))

    def count_items(self) -> int:
        with self.db.get_session() as session:
            return int(session.scalar(select(func.count()).select_from(CSItemCatalog)) or 0)

    def get_state(self) -> CSItemCatalogState:
        with self.db.get_session() as session:
            row = session.get(CSItemCatalogState, 1)
            if row is None:
                row = CSItemCatalogState(id=1)
                session.add(row)
                session.commit()
                session.refresh(row)
            return row

    def _refresh_item_count(self, session) -> None:
        state = session.get(CSItemCatalogState, 1)
        if state is None:
            state = CSItemCatalogState(id=1)
            session.add(state)
        state.item_count = int(
            session.scalar(select(func.count()).select_from(CSItemCatalog)) or 0
        )
        state.updated_at = datetime.now()

    def upsert_entries(self, entries: List[Dict[str, Any]]) -> int:
        if not entries:
            return 0
        now = datetime.now()
        rows: List[Dict[str, Any]] = []
        for entry in entries:
            good_id = int(entry["good_id"])
            name = str(entry.get("name") or good_id)
            market_hash_name = str(entry.get("market_hash_name") or name)
            rows.append(
                {
                    "good_id": good_id,
                    "name": name,
                    "market_hash_name": market_hash_name,
                    "search_blob": _normalize_search_blob(name, market_hash_name),
                    "item_type": str(entry.get("item_type") or ""),
                    "last_synced_at": now,
                    "updated_at": now,
                }
            )

        with self.db.get_session() as session:
            for row in rows:
                stmt = sqlite_insert(CSItemCatalog).values(
                    **row,
                    first_seen_at=now,
                )
                stmt = stmt.on_conflict_do_update(
                    index_elements=[CSItemCatalog.good_id],
                    set_={
                        "name": stmt.excluded.name,
                        "market_hash_name": stmt.excluded.market_hash_name,
                        "search_blob": stmt.excluded.search_blob,
                        "item_type": stmt.excluded.item_type,
                        "last_synced_at": stmt.excluded.last_synced_at,
                        "updated_at": stmt.excluded.updated_at,
                    },
                )
                session.execute(stmt)
            self._refresh_item_count(session)
            session.commit()
        return len(rows)

    def search_items(
        self,
        search: str,
        *,
        page_index: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[CSItemCatalog], int]:
        term = (search or "").strip()
        if not term:
            return [], 0

        page_index = max(1, int(page_index))
        page_size = max(1, min(int(page_size), 50))
        offset = (page_index - 1) * page_size
        lowered = term.lower()

        with self.db.get_session() as session:
            if term.isdigit():
                good_id = int(term)
                exact = session.get(CSItemCatalog, good_id)
                if exact is not None:
                    return [exact], 1

            filters = [
                CSItemCatalog.name.ilike(f"%{term}%"),
                CSItemCatalog.market_hash_name.ilike(f"%{term}%"),
                CSItemCatalog.search_blob.ilike(f"%{lowered}%"),
            ]
            where_clause = or_(*filters)
            total = int(session.scalar(select(func.count()).select_from(CSItemCatalog).where(where_clause)) or 0)
            rows = session.execute(
                select(CSItemCatalog)
                .where(where_clause)
                .order_by(
                    CSItemCatalog.name.asc(),
                    CSItemCatalog.good_id.asc(),
                )
                .offset(offset)
                .limit(page_size)
            ).scalars().all()
            return list(rows), total

    def update_sync_state(
        self,
        *,
        api_total: Optional[int] = None,
        last_full_sync_at: Optional[datetime] = None,
        last_incremental_sync_at: Optional[datetime] = None,
        last_sync_status: Optional[str] = None,
        last_sync_mode: Optional[str] = None,
        checkpoint_page: Optional[int] = None,
        checkpoint_mode: Optional[str] = None,
        last_error: Optional[str] = None,
        clear_checkpoint: bool = False,
    ) -> CSItemCatalogState:
        with self.db.get_session() as session:
            state = session.get(CSItemCatalogState, 1)
            if state is None:
                state = CSItemCatalogState(id=1)
                session.add(state)
            if api_total is not None:
                state.api_total = int(api_total)
            if last_full_sync_at is not None:
                state.last_full_sync_at = last_full_sync_at
            if last_incremental_sync_at is not None:
                state.last_incremental_sync_at = last_incremental_sync_at
            if last_sync_status is not None:
                state.last_sync_status = last_sync_status
            if last_sync_mode is not None:
                state.last_sync_mode = last_sync_mode
            if checkpoint_page is not None:
                state.checkpoint_page = int(checkpoint_page)
            if checkpoint_mode is not None:
                state.checkpoint_mode = checkpoint_mode
            if last_error is not None:
                state.last_error = last_error
            if clear_checkpoint:
                state.checkpoint_page = 0
                state.checkpoint_mode = ''
            self._refresh_item_count(session)
            state.updated_at = datetime.now()
            session.commit()
            session.refresh(state)
            return state
