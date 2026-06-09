# -*- coding: utf-8 -*-
"""CS inventory holdings: manual entry, image import, snapshot P&L."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from market_provider.csqaq.client import CSQAQClient, resolve_price_platform
from market_provider.csqaq.item_analysis import fetch_item_snapshot
from src.repositories.cs_holdings_repo import CSHoldingsRepository
from src.services.cs_holdings_dedup import attach_dedup_fields, reconcile_item_name_and_wear
from src.services.cs_holdings_match_engine import match_holding_item
from src.services.image_cs_holdings_extractor import extract_cs_holdings_from_image

logger = logging.getLogger(__name__)


def _sync_auto_alerts() -> None:
    from src.services.cs_auto_alerts_service import maybe_sync_cs_auto_alerts

    maybe_sync_cs_auto_alerts()


def _platform_name(value: Any) -> str:
    plat = resolve_price_platform(value or "yyyp")
    return plat.name.lower() if hasattr(plat, "name") else str(plat).lower()

_PLATFORM_PRICE_KEYS = {
    "buff": "buff_sell_price",
    "yyyp": "yyyp_sell_price",
    "steam": "steam_sell_price",
}


def _pick_market_price(snapshot: Dict[str, Any], platform: str) -> Optional[float]:
    key = _PLATFORM_PRICE_KEYS.get((platform or "yyyp").lower(), "yyyp_sell_price")
    value = snapshot.get(key)
    if value is not None:
        try:
            return float(value)
        except (TypeError, ValueError):
            pass
    for fallback in ("yyyp_sell_price", "buff_sell_price", "steam_sell_price"):
        raw = snapshot.get(fallback)
        if raw is not None:
            try:
                return float(raw)
            except (TypeError, ValueError):
                continue
    return None


def _thumbnail_from_snapshot(snapshot: Dict[str, Any]) -> Optional[str]:
    for key in ("icon_url", "img_url", "image_url", "goods_img"):
        value = snapshot.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


class CSHoldingsService:
    def __init__(self, repo: Optional[CSHoldingsRepository] = None):
        self.repo = repo or CSHoldingsRepository()

    def _resolve_good_id(self, item_name: str, wear: str = "") -> Optional[int]:
        match = match_holding_item(item_name=item_name, wear=wear)
        return match.good_id

    def rematch_missing_good_ids(self) -> Dict[str, Any]:
        """Backfill good_id for holdings imported before match improvements."""
        rows = self.repo.list_without_good_id()
        matched = 0
        failed: List[Dict[str, Any]] = []
        for row in rows:
            match = match_holding_item(item_name=row.item_name, wear=row.wear or "")
            if match.good_id is None:
                failed.append({"id": row.id, "item_name": row.item_name})
                continue
            payload = attach_dedup_fields(
                {
                    "good_id": int(match.good_id),
                    "item_name": match.item_name or row.item_name,
                    "market_hash_name": match.market_hash_name or row.market_hash_name or "",
                    "wear": row.wear or "",
                    "float_value": row.float_value,
                    "platform": row.platform or "yyyp",
                }
            )
            updated = self.repo.update(
                row.id,
                {
                    "good_id": payload["good_id"],
                    "item_name": payload.get("item_name", row.item_name),
                    "market_hash_name": payload.get("market_hash_name", row.market_hash_name or ""),
                    "wear": payload.get("wear", row.wear or ""),
                    "dedup_key": payload["dedup_key"],
                },
            )
            if updated is not None:
                matched += 1
        return {
            "attempted": len(rows),
            "matched": matched,
            "failed": failed[:20],
        }

    def _refresh_row_prices(self, row: Any) -> Dict[str, Any]:
        platform = (row.platform or "yyyp").lower()
        item_name, wear = reconcile_item_name_and_wear(row.item_name or "", row.wear or "")
        if wear != (row.wear or ""):
            repaired = attach_dedup_fields(
                {
                    "item_name": item_name,
                    "wear": wear,
                    "float_value": row.float_value,
                    "platform": platform,
                }
            )
            try:
                self.repo.update(
                    row.id,
                    {"wear": wear, "dedup_key": repaired["dedup_key"]},
                )
                row.wear = wear
            except Exception as exc:
                logger.debug("CS holdings wear repair skipped id=%s: %s", row.id, exc)

        market_price = row.market_price
        thumbnail_url = row.thumbnail_url
        good_id = row.good_id

        if good_id:
            try:
                snapshot = fetch_item_snapshot(CSQAQClient(), int(good_id))
                live = _pick_market_price(snapshot, platform)
                if live is not None:
                    market_price = live
                thumb = _thumbnail_from_snapshot(snapshot)
                if thumb:
                    thumbnail_url = thumb
            except Exception as exc:
                logger.debug("CS holdings price refresh failed good_id=%s: %s", good_id, exc)

        qty = max(1, int(row.quantity or 1))
        purchase = float(row.purchase_price or 0)
        cost_total = purchase * qty
        market_total = float(market_price or 0) * qty if market_price is not None else None
        pnl = (market_total - cost_total) if market_total is not None else None
        pnl_pct = ((pnl / cost_total) * 100.0) if pnl is not None and cost_total > 0 else None

        return {
            "id": row.id,
            "good_id": good_id,
            "item_name": item_name,
            "market_hash_name": row.market_hash_name or "",
            "wear": wear,
            "float_value": row.float_value,
            "platform": platform,
            "quantity": qty,
            "purchase_price": purchase,
            "market_price": market_price,
            "cost_total": round(cost_total, 2),
            "market_total": round(market_total, 2) if market_total is not None else None,
            "pnl": round(pnl, 2) if pnl is not None else None,
            "pnl_pct": round(pnl_pct, 2) if pnl_pct is not None else None,
            "thumbnail_url": thumbnail_url,
            "note": row.note,
            "dedup_key": row.dedup_key,
            "import_batch_id": row.import_batch_id,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        }

    def get_snapshot(
        self,
        *,
        refresh_prices: bool = True,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        platform: Optional[str] = None,
        sort: str = "updated_at",
    ) -> Dict[str, Any]:
        rematch_summary: Optional[Dict[str, Any]] = None
        if refresh_prices:
            rematch_summary = self.rematch_missing_good_ids()

        if page is not None and page_size is not None:
            rows, total = self.repo.list_paginated(
                page=page,
                page_size=page_size,
                platform=platform,
                sort=sort,
            )
            paginated = True
        else:
            rows = self.repo.list_all(platform=platform)
            total = len(rows)
            paginated = False

        all_rows = self.repo.list_all(platform=platform) if paginated else rows
        items: List[Dict[str, Any]] = []
        total_market = 0.0
        total_cost = 0.0
        total_pnl = 0.0
        has_market = False

        for row in rows:
            item = self._refresh_row_prices(row) if refresh_prices else self._serialize_row(row)
            items.append(item)

        for row in all_rows:
            item = self._refresh_row_prices(row) if refresh_prices else self._serialize_row(row)
            total_cost += float(item.get("cost_total") or 0)
            if item.get("market_total") is not None:
                has_market = True
                total_market += float(item["market_total"])
                if item.get("pnl") is not None:
                    total_pnl += float(item["pnl"])

        item_count = sum(max(1, int(getattr(r, "quantity", 1) or 1)) for r in all_rows)

        payload: Dict[str, Any] = {
            "summary": {
                "item_count": item_count,
                "row_count": len(all_rows),
                "total_market_value": round(total_market, 2) if has_market else None,
                "total_cost": round(total_cost, 2),
                "total_pnl": round(total_pnl, 2) if has_market else None,
            },
            "items": items,
        }
        if rematch_summary and rematch_summary.get("attempted"):
            payload["good_id_rematch"] = rematch_summary
        if paginated:
            payload["pagination"] = {
                "page": page,
                "page_size": page_size,
                "total": total,
            }
        return payload

    def _serialize_row(self, row: Any) -> Dict[str, Any]:
        return self._refresh_row_prices(row)

    def create_holding(
        self,
        *,
        item_name: str,
        good_id: Optional[int] = None,
        market_hash_name: str = "",
        wear: str = "",
        float_value: Optional[float] = None,
        platform: Optional[str] = None,
        quantity: int = 1,
        purchase_price: float = 0.0,
        market_price: Optional[float] = None,
        note: str = "",
    ) -> Dict[str, Any]:
        name = (item_name or "").strip()
        if not name:
            raise ValueError("item_name is required")
        name, wear = reconcile_item_name_and_wear(name, wear or "")
        plat = _platform_name(platform or "yyyp")
        gid = good_id or self._resolve_good_id(name, wear)
        row = self.repo.create(
            attach_dedup_fields(
                {
                    "good_id": gid,
                    "item_name": name,
                    "market_hash_name": market_hash_name or "",
                    "wear": wear or "",
                    "float_value": float_value,
                    "platform": plat,
                    "quantity": max(1, int(quantity)),
                    "purchase_price": float(purchase_price or 0),
                    "market_price": market_price,
                    "note": (note or "")[:255],
                }
            )
        )
        row = self._refresh_row_prices(row)
        _sync_auto_alerts()
        return row

    def update_holding(self, holding_id: int, **fields: Any) -> Dict[str, Any]:
        allowed = {
            "good_id",
            "item_name",
            "market_hash_name",
            "wear",
            "float_value",
            "platform",
            "quantity",
            "purchase_price",
            "market_price",
            "note",
        }
        payload = {k: v for k, v in fields.items() if k in allowed and v is not None}
        if "platform" in payload:
            payload["platform"] = _platform_name(str(payload["platform"]))
        if "quantity" in payload:
            payload["quantity"] = max(1, int(payload["quantity"]))
        if any(k in payload for k in ("item_name", "wear", "float_value", "platform")):
            row_before = self.repo.get(holding_id)
            if row_before is not None:
                merged_name = payload.get("item_name", row_before.item_name)
                merged_wear = payload.get("wear", row_before.wear)
                item_name, wear = reconcile_item_name_and_wear(
                    str(merged_name or ""),
                    str(merged_wear or ""),
                )
                payload["item_name"] = item_name
                payload["wear"] = wear
                dedup_payload = attach_dedup_fields(
                    {
                        "item_name": item_name,
                        "wear": wear,
                        "float_value": payload.get("float_value", row_before.float_value),
                        "platform": payload.get("platform", row_before.platform),
                    }
                )
                payload["dedup_key"] = dedup_payload["dedup_key"]
        row = self.repo.update(holding_id, payload)
        if row is None:
            raise ValueError("holding not found")
        refreshed = self._refresh_row_prices(row)
        _sync_auto_alerts()
        return refreshed

    def delete_holding(self, holding_id: int) -> None:
        row = self.repo.get(holding_id)
        if row is None:
            raise ValueError("holding not found")
        if not self.repo.delete(holding_id):
            raise ValueError("holding not found")
        _sync_auto_alerts()

    def bulk_create(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        payloads: List[Dict[str, Any]] = []
        for raw in items:
            name = str(raw.get("item_name") or "").strip()
            if not name:
                continue
            wear_text = str(raw.get("wear") or "")
            name, wear_text = reconcile_item_name_and_wear(name, wear_text)
            plat = _platform_name(str(raw.get("platform") or "yyyp"))
            gid = raw.get("good_id") or self._resolve_good_id(name, wear_text)
            payloads.append(
                attach_dedup_fields(
                    {
                        "good_id": int(gid) if gid is not None else None,
                        "item_name": name,
                        "market_hash_name": str(raw.get("market_hash_name") or ""),
                        "wear": wear_text,
                        "float_value": raw.get("float_value"),
                        "platform": plat,
                        "quantity": max(1, int(raw.get("quantity") or 1)),
                        "purchase_price": float(raw.get("purchase_price") or 0),
                        "market_price": raw.get("market_price"),
                        "note": str(raw.get("note") or "")[:255],
                    }
                )
            )
        if not payloads:
            return []
        rows = self.repo.bulk_create(payloads)
        refreshed = [self._refresh_row_prices(row) for row in rows]
        _sync_auto_alerts()
        return refreshed

    def extract_from_image(self, image_bytes: bytes, mime_type: str) -> Dict[str, Any]:
        parsed, raw_text = extract_cs_holdings_from_image(image_bytes, mime_type)
        enriched_items: List[Dict[str, Any]] = []
        for item in parsed.get("items") or []:
            name = str(item.get("item_name") or "").strip()
            gid = self._resolve_good_id(name) if name else None
            enriched_items.append({**item, "good_id": gid})
        return {
            "summary": parsed.get("summary") or {},
            "items": enriched_items,
            "raw_text": raw_text,
        }
