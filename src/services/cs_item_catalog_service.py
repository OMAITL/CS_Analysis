# -*- coding: utf-8 -*-
"""CSQAQ item catalog sync and local search."""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from market_provider.csqaq.client import CSQAQClient
from market_provider.csqaq.schemas import GoodIdEntry
from src.repositories.cs_item_catalog_repo import CSItemCatalogRepository

logger = logging.getLogger(__name__)


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw.strip())
    except ValueError:
        return default


def _catalog_row_from_api(row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    raw_id = row.get("id") if row.get("id") is not None else row.get("good_id")
    if raw_id is None:
        return None
    try:
        good_id = int(raw_id)
    except (TypeError, ValueError):
        return None
    name = str(row.get("name") or row.get("goods_name") or good_id)
    market_hash_name = str(
        row.get("market_hash_name") or row.get("marketHashName") or name
    )
    item_type = str(row.get("type") or row.get("goods_type") or "")
    return {
        "good_id": good_id,
        "name": name,
        "market_hash_name": market_hash_name,
        "item_type": item_type,
    }


def _serialize_catalog_item(row) -> Dict[str, Any]:
    return {
        "good_id": int(row.good_id),
        "name": str(row.name),
        "market_hash_name": str(row.market_hash_name or ""),
    }


class CSItemCatalogService:
    def __init__(
        self,
        repo: Optional[CSItemCatalogRepository] = None,
        client: Optional[CSQAQClient] = None,
    ):
        self.repo = repo or CSItemCatalogRepository()
        self._client = client

    @property
    def page_size(self) -> int:
        return max(20, min(_env_int("CS_ITEM_CATALOG_SYNC_PAGE_SIZE", 100), 500))

    @property
    def incremental_tail_pages(self) -> int:
        return max(1, _env_int("CS_ITEM_CATALOG_INCREMENTAL_TAIL_PAGES", 3))

    @property
    def local_search_enabled(self) -> bool:
        return _env_bool("CS_ITEM_CATALOG_LOCAL_SEARCH", True)

    @property
    def min_local_results(self) -> int:
        return max(1, _env_int("CS_ITEM_CATALOG_MIN_LOCAL_RESULTS", 1))

    @property
    def upsert_on_remote(self) -> bool:
        return _env_bool("CS_ITEM_CATALOG_UPSERT_ON_REMOTE", True)

    def _get_client(self) -> CSQAQClient:
        if self._client is None:
            self._client = CSQAQClient(enable_cache=False)
        return self._client

    def get_status(self) -> Dict[str, Any]:
        state = self.repo.get_state()
        return {
            "item_count": int(state.item_count or 0),
            "api_total": int(state.api_total or 0),
            "last_full_sync_at": state.last_full_sync_at.isoformat() if state.last_full_sync_at else None,
            "last_incremental_sync_at": (
                state.last_incremental_sync_at.isoformat() if state.last_incremental_sync_at else None
            ),
            "last_sync_status": state.last_sync_status or "idle",
            "last_sync_mode": state.last_sync_mode or "",
            "checkpoint_page": int(state.checkpoint_page or 0),
            "checkpoint_mode": state.checkpoint_mode or "",
            "last_error": state.last_error or "",
            "local_search_enabled": self.local_search_enabled,
        }

    def upsert_good_id_entries(self, entries: List[GoodIdEntry | Dict[str, Any]]) -> int:
        rows: List[Dict[str, Any]] = []
        for entry in entries:
            if isinstance(entry, GoodIdEntry):
                rows.append(
                    {
                        "good_id": int(entry.id),
                        "name": entry.name,
                        "market_hash_name": entry.market_hash_name,
                    }
                )
            elif isinstance(entry, dict) and entry.get("good_id") is not None:
                rows.append(entry)
        return self.repo.upsert_entries(rows)

    def search_local(
        self,
        search: str,
        *,
        page_index: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        rows, total = self.repo.search_items(search, page_index=page_index, page_size=page_size)
        return {
            "items": [_serialize_catalog_item(row) for row in rows],
            "page_index": page_index,
            "page_size": page_size,
            "total": total,
            "source": "local",
        }

    def search_hybrid(
        self,
        search: str,
        *,
        page_index: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        term = (search or "").strip()
        if not term:
            raise ValueError("search is required")

        if self.local_search_enabled and self.repo.count_items() > 0:
            local_payload = self.search_local(term, page_index=page_index, page_size=page_size)
            if int(local_payload.get("total") or 0) >= self.min_local_results:
                return local_payload

        client = self._get_client()
        result = client.search_goods(
            term,
            page_index=max(1, int(page_index)),
            page_size=max(1, min(int(page_size), 50)),
        )
        items = [
            {
                "good_id": int(entry.id),
                "name": str(entry.name),
                "market_hash_name": str(entry.market_hash_name),
            }
            for entry in result.items
        ]
        remote_payload = {
            "items": items,
            "page_index": int(result.page_index),
            "page_size": int(result.page_size),
            "total": int(result.total),
            "source": "csqaq",
        }
        if self.upsert_on_remote and items:
            try:
                self.upsert_good_id_entries(items)
            except Exception as exc:
                logger.debug("CS catalog upsert from remote search failed: %s", exc)
        return remote_payload

    def _upsert_page_payload(self, payload: Dict[str, Any]) -> int:
        raw_rows = list(payload.get("data") or [])
        entries = []
        for row in raw_rows:
            if isinstance(row, dict):
                parsed = _catalog_row_from_api(row)
                if parsed:
                    entries.append(parsed)
        return self.repo.upsert_entries(entries)

    def _fetch_page(self, page_index: int) -> Dict[str, Any]:
        return self._get_client().get_page_list(page_index=page_index, page_size=self.page_size)

    def sync_full(
        self,
        *,
        resume: bool = False,
        max_pages: Optional[int] = None,
    ) -> Dict[str, Any]:
        state = self.repo.get_state()
        start_page = max(1, int(state.checkpoint_page or 1)) if resume and state.checkpoint_mode == "full" else 1
        self.repo.update_sync_state(
            last_sync_status="running",
            last_sync_mode="full",
            checkpoint_page=start_page,
            checkpoint_mode="full",
            last_error="",
        )

        pages_fetched = 0
        rows_upserted = 0
        api_total = 0
        page_index = start_page

        try:
            while True:
                if max_pages is not None and pages_fetched >= max_pages:
                    break
                payload = self._fetch_page(page_index)
                api_total = int(payload.get("total") or api_total or 0)
                batch = self._upsert_page_payload(payload)
                pages_fetched += 1
                if batch == 0:
                    break
                rows_upserted += batch
                self.repo.update_sync_state(
                    api_total=api_total,
                    checkpoint_page=page_index + 1,
                    checkpoint_mode="full",
                )
                page_index += 1

            finished_at = datetime.now()
            if max_pages is None:
                self.repo.update_sync_state(
                    api_total=api_total,
                    last_full_sync_at=finished_at,
                    last_sync_status="completed",
                    last_sync_mode="full",
                    clear_checkpoint=True,
                    last_error="",
                )
            else:
                self.repo.update_sync_state(
                    api_total=api_total,
                    last_sync_status="completed",
                    last_sync_mode="full",
                    checkpoint_page=page_index,
                    checkpoint_mode="full",
                    last_error="",
                )
            logger.info(
                "CS catalog full sync done: pages=%s rows=%s api_total=%s",
                pages_fetched,
                rows_upserted,
                api_total,
            )
            return {
                "mode": "full",
                "pages_fetched": pages_fetched,
                "rows_upserted": rows_upserted,
                "api_total": api_total,
                "resume": resume,
                "max_pages": max_pages,
                "completed": max_pages is None,
            }
        except Exception as exc:
            logger.error("CS catalog full sync failed at page=%s: %s", page_index, exc, exc_info=True)
            self.repo.update_sync_state(
                last_sync_status="failed",
                last_sync_mode="full",
                checkpoint_page=page_index,
                checkpoint_mode="full",
                last_error=str(exc),
            )
            raise

    def sync_incremental(self, *, max_pages: Optional[int] = None) -> Dict[str, Any]:
        local_count = self.repo.count_items()
        state = self.repo.get_state()
        if local_count == 0 or state.last_full_sync_at is None:
            logger.info("CS catalog incremental requested but no full baseline; running full sync")
            return self.sync_full(resume=False, max_pages=max_pages)

        self.repo.update_sync_state(
            last_sync_status="running",
            last_sync_mode="incremental",
            last_error="",
        )

        pages_fetched = 0
        rows_upserted = 0
        page_size = self.page_size

        try:
            first_payload = self._fetch_page(1)
            api_total = int(first_payload.get("total") or 0)
            rows_upserted += self._upsert_page_payload(first_payload)
            pages_fetched += 1

            old_api_total = int(state.api_total or 0)
            total_pages = max(1, (api_total + page_size - 1) // page_size) if api_total > 0 else 1
            pages_to_sync: List[int] = []

            if api_total > old_api_total > 0:
                start_page = max(2, (old_api_total // page_size) + 1)
                pages_to_sync.extend(range(start_page, total_pages + 1))
            else:
                tail_start = max(1, total_pages - self.incremental_tail_pages + 1)
                pages_to_sync.extend(range(tail_start, total_pages + 1))

            seen = {1}
            for page_index in pages_to_sync:
                if page_index in seen:
                    continue
                if max_pages is not None and pages_fetched >= max_pages:
                    break
                payload = self._fetch_page(page_index)
                batch = self._upsert_page_payload(payload)
                rows_upserted += batch
                pages_fetched += 1
                seen.add(page_index)

            finished_at = datetime.now()
            self.repo.update_sync_state(
                api_total=api_total,
                last_incremental_sync_at=finished_at,
                last_sync_status="completed",
                last_sync_mode="incremental",
                clear_checkpoint=True,
                last_error="",
            )
            logger.info(
                "CS catalog incremental sync done: pages=%s rows=%s api_total=%s",
                pages_fetched,
                rows_upserted,
                api_total,
            )
            return {
                "mode": "incremental",
                "pages_fetched": pages_fetched,
                "rows_upserted": rows_upserted,
                "api_total": api_total,
                "previous_api_total": old_api_total,
                "max_pages": max_pages,
            }
        except Exception as exc:
            logger.error("CS catalog incremental sync failed: %s", exc, exc_info=True)
            self.repo.update_sync_state(
                last_sync_status="failed",
                last_sync_mode="incremental",
                last_error=str(exc),
            )
            raise

    def sync(self, mode: str = "incremental", **kwargs) -> Dict[str, Any]:
        normalized = (mode or "incremental").strip().lower()
        if normalized == "full":
            return self.sync_full(**kwargs)
        return self.sync_incremental(**kwargs)
