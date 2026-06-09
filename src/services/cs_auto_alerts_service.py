# -*- coding: utf-8 -*-
"""Auto-sync CS holdings alert rules from portfolio state."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

from src.config import Config, get_config
from src.repositories.alert_repo import AlertRepository
from src.repositories.cs_holdings_repo import CSHoldingsRepository
from src.services.alert_service import AlertService


logger = logging.getLogger(__name__)

CS_AUTO_ALERT_SOURCE = "cs_auto"
CS_AUTO_NAME_PREFIX = "cs_auto:"
CS_AUTO_DISPLAY_NAME_PREFIX = "CS 自动"
CS_AUTO_SYNC_PAGE_SIZE = 100


@dataclass(frozen=True)
class _AutoRuleSpec:
    name: str
    target_scope: str
    target: str
    alert_type: str
    parameters: Dict[str, Any]
    display_name: str
    severity: str = "warning"


@dataclass(frozen=True)
class _AggregatedHoldingLot:
    good_id: int
    platform: str
    item_name: str
    avg_purchase_price: float
    total_quantity: int
    lot_count: int


class CSAutoAlertsService:
    """Ensure CS alert rules exist automatically; no manual /alerts setup required."""

    def __init__(
        self,
        *,
        holdings_repo: Optional[CSHoldingsRepository] = None,
        alert_service: Optional[AlertService] = None,
        alert_repo: Optional[AlertRepository] = None,
        config: Optional[Config] = None,
    ):
        self.holdings_repo = holdings_repo or CSHoldingsRepository()
        self.alert_service = alert_service or AlertService()
        self.alert_repo = alert_repo or AlertRepository()
        self.config = config or get_config()

    def is_enabled(self) -> bool:
        return bool(getattr(self.config, "cs_holdings_auto_alerts_enabled", True))

    def sync(self) -> Dict[str, int]:
        """Create/update/delete cs_auto rules to match current holdings."""
        stats = {"created": 0, "updated": 0, "deleted": 0, "skipped": 0}
        stats["deleted"] += self.cleanup_orphan_cs_item_price_rules()
        if not self.is_enabled():
            return stats

        expected = self._build_expected_rules()
        expected_keys = {self._rule_key(spec): spec for spec in expected}
        managed_rows = self._list_managed_auto_rows()
        stats["deleted"] += self._prune_duplicate_managed_rows(managed_rows)

        existing_by_key: Dict[Tuple[str, str, str, str], Any] = {}
        for row in managed_rows:
            key = self._row_key(row)
            current = existing_by_key.get(key)
            if current is None or int(row.id) > int(current.id):
                existing_by_key[key] = row

        for key, spec in expected_keys.items():
            existing = existing_by_key.get(key)
            if existing is None:
                try:
                    payload = {
                        "name": spec.display_name,
                        "target_scope": spec.target_scope,
                        "target": spec.target,
                        "alert_type": spec.alert_type,
                        "parameters": spec.parameters,
                        "severity": spec.severity,
                        "enabled": True,
                        "source": CS_AUTO_ALERT_SOURCE,
                    }
                    self.alert_service.create_rule(payload)
                    stats["created"] += 1
                except Exception as exc:
                    logger.warning("[CSAutoAlerts] create failed for %s: %s", spec.name, exc)
                    stats["skipped"] += 1
                continue

            updates = self._diff_rule_updates(existing, spec)
            if updates:
                try:
                    self.alert_repo.update_rule(int(existing.id), updates)
                    stats["updated"] += 1
                except Exception as exc:
                    logger.warning("[CSAutoAlerts] update failed for %s: %s", spec.name, exc)
                    stats["skipped"] += 1

        for row in managed_rows:
            if self._row_key(row) not in expected_keys:
                try:
                    self.alert_repo.delete_rule(int(row.id))
                    stats["deleted"] += 1
                except Exception as exc:
                    logger.warning("[CSAutoAlerts] delete failed for rule %s: %s", row.id, exc)
                    stats["skipped"] += 1

        if any(stats[key] > 0 for key in ("created", "updated", "deleted")):
            logger.info(
                "[CSAutoAlerts] sync complete created=%s updated=%s deleted=%s",
                stats["created"],
                stats["updated"],
                stats["deleted"],
            )
        return stats

    def cleanup_orphan_cs_item_price_rules(self) -> int:
        """Delete cs_item price-cross rules whose good_id/platform no longer has holdings."""
        holdings = self.holdings_repo.list_all()
        active_lots = active_cs_item_lots(holdings)
        active_good_ids = {good_id for good_id, _ in active_lots}
        deleted = 0
        page = 1
        while True:
            batch, total = self.alert_repo.list_rules(
                target_scope="cs_item",
                alert_type="cs_price_cross",
                page=page,
                page_size=CS_AUTO_SYNC_PAGE_SIZE,
            )
            for row in batch:
                if not _is_orphan_cs_item_price_rule(row, active_lots, active_good_ids):
                    continue
                try:
                    if self.alert_repo.delete_rule(int(row.id)):
                        deleted += 1
                except Exception as exc:
                    logger.warning(
                        "[CSAutoAlerts] orphan cs_item rule delete failed for %s: %s",
                        row.id,
                        exc,
                    )
            if page * CS_AUTO_SYNC_PAGE_SIZE >= total:
                break
            page += 1
        return deleted

    def _build_expected_rules(self) -> List[_AutoRuleSpec]:
        specs: List[_AutoRuleSpec] = []
        specs.extend(self._portfolio_level_rules())
        specs.extend(self._holding_price_rules())
        return specs

    def _portfolio_level_rules(self) -> List[_AutoRuleSpec]:
        if not getattr(self.config, "cs_auto_portfolio_alerts_enabled", True):
            return []
        return [
            _AutoRuleSpec(
                name=f"{CS_AUTO_NAME_PREFIX}portfolio:stop_loss",
                target_scope="cs_holdings",
                target="all",
                alert_type="cs_stop_loss",
                parameters={"mode": "near"},
                display_name="CS 自动止损监控",
            ),
            _AutoRuleSpec(
                name=f"{CS_AUTO_NAME_PREFIX}portfolio:concentration",
                target_scope="cs_holdings",
                target="all",
                alert_type="cs_concentration",
                parameters={},
                display_name="CS 自动集中度监控",
            ),
            _AutoRuleSpec(
                name=f"{CS_AUTO_NAME_PREFIX}portfolio:price_stale",
                target_scope="cs_holdings",
                target="all",
                alert_type="cs_price_stale",
                parameters={},
                display_name="CS 自动价格状态监控",
                severity="info",
            ),
        ]

    def _holding_price_rules(self) -> List[_AutoRuleSpec]:
        if not getattr(self.config, "cs_auto_price_alerts_enabled", True):
            return []
        take_profit_pct = float(getattr(self.config, "cs_auto_price_alert_take_profit_pct", 20.0))
        stop_loss_pct = float(getattr(self.config, "cs_auto_price_alert_stop_loss_pct", 10.0))
        if take_profit_pct <= 0 and stop_loss_pct <= 0:
            return []

        rows = self.holdings_repo.list_all()
        specs: List[_AutoRuleSpec] = []
        for lot in aggregate_holdings_for_price_alerts(rows):
            purchase_price = lot.avg_purchase_price
            item_name = lot.item_name
            platform = lot.platform
            good_id = lot.good_id
            name_suffix = (
                f" · 均价 {purchase_price:.2f}"
                if lot.lot_count > 1
                else ""
            )

            if take_profit_pct > 0:
                tp_price = round(purchase_price * (1.0 + take_profit_pct / 100.0), 2)
                specs.append(
                    _AutoRuleSpec(
                        name=f"{CS_AUTO_NAME_PREFIX}item:{good_id}:{platform}:take_profit",
                        target_scope="cs_item",
                        target=str(good_id),
                        alert_type="cs_price_cross",
                        parameters={"direction": "above", "price": tp_price, "platform": platform},
                        display_name=f"CS 自动止盈 · {item_name} ≥ {tp_price}{name_suffix}",
                    )
                )
            if stop_loss_pct > 0:
                sl_price = round(purchase_price * (1.0 - stop_loss_pct / 100.0), 2)
                if sl_price > 0:
                    specs.append(
                        _AutoRuleSpec(
                            name=f"{CS_AUTO_NAME_PREFIX}item:{good_id}:{platform}:stop_loss",
                            target_scope="cs_item",
                            target=str(good_id),
                            alert_type="cs_price_cross",
                            parameters={"direction": "below", "price": sl_price, "platform": platform},
                            display_name=f"CS 自动止损 · {item_name} ≤ {sl_price}{name_suffix}",
                            severity="critical",
                        )
                    )
        return specs

    def _list_managed_auto_rows(self) -> List[Any]:
        rows: List[Any] = []
        page = 1
        while True:
            batch, total = self.alert_repo.list_rules(
                cs_only=True,
                page=page,
                page_size=CS_AUTO_SYNC_PAGE_SIZE,
            )
            rows.extend(row for row in batch if self._is_managed_auto_row(row))
            if page * CS_AUTO_SYNC_PAGE_SIZE >= total:
                break
            page += 1
        return rows

    @staticmethod
    def _is_managed_auto_row(row: Any) -> bool:
        scope = str(getattr(row, "target_scope", "") or "")
        if scope not in {"cs_holdings", "cs_item"}:
            return False
        source = str(getattr(row, "source", "") or "")
        if source == CS_AUTO_ALERT_SOURCE:
            return True
        name = str(getattr(row, "name", "") or "")
        return name.startswith(CS_AUTO_DISPLAY_NAME_PREFIX)

    def _prune_duplicate_managed_rows(self, rows: List[Any]) -> int:
        grouped: Dict[Tuple[str, str, str, str], List[Any]] = {}
        for row in rows:
            grouped.setdefault(self._row_key(row), []).append(row)

        deleted = 0
        for group in grouped.values():
            if len(group) <= 1:
                continue
            keep = max(group, key=lambda item: int(item.id))
            for row in group:
                if int(row.id) == int(keep.id):
                    continue
                try:
                    if self.alert_repo.delete_rule(int(row.id)):
                        deleted += 1
                except Exception as exc:
                    logger.warning("[CSAutoAlerts] duplicate delete failed for rule %s: %s", row.id, exc)
        return deleted

    @staticmethod
    def _rule_key(spec: _AutoRuleSpec) -> Tuple[str, str, str, str]:
        canonical = json.dumps(spec.parameters or {}, ensure_ascii=False, sort_keys=True)
        return (spec.target_scope, spec.target, spec.alert_type, canonical)

    @staticmethod
    def _row_key(row: Any) -> Tuple[str, str, str, str]:
        params = _load_json_dict(getattr(row, "parameters", None))
        canonical = json.dumps(params, ensure_ascii=False, sort_keys=True)
        return (str(row.target_scope), str(row.target), str(row.alert_type), canonical)

    @staticmethod
    def _diff_rule_updates(existing: Any, spec: _AutoRuleSpec) -> Dict[str, Any]:
        updates: Dict[str, Any] = {}
        if str(existing.name) != spec.display_name:
            updates["name"] = spec.display_name
        if str(existing.severity) != spec.severity:
            updates["severity"] = spec.severity
        return updates


def aggregate_holdings_for_price_alerts(rows: List[Any]) -> List[_AggregatedHoldingLot]:
    """Merge duplicate good_id rows (per platform) using quantity-weighted average cost."""

    buckets: Dict[Tuple[int, str], Dict[str, Any]] = {}
    for row in rows:
        good_id = getattr(row, "good_id", None)
        purchase_price = float(getattr(row, "purchase_price", 0.0) or 0.0)
        if good_id is None or purchase_price <= 0:
            continue
        try:
            gid = int(good_id)
        except (TypeError, ValueError):
            continue
        if gid <= 0:
            continue

        platform = str(getattr(row, "platform", None) or "yyyp").lower()
        qty = max(1, int(getattr(row, "quantity", 1) or 1))
        item_name = str(getattr(row, "item_name", "") or gid).strip() or str(gid)
        key = (gid, platform)
        bucket = buckets.get(key)
        if bucket is None:
            buckets[key] = {
                "good_id": gid,
                "platform": platform,
                "item_name": item_name,
                "cost_sum": purchase_price * qty,
                "qty_sum": qty,
                "lot_count": 1,
            }
            continue

        bucket["cost_sum"] += purchase_price * qty
        bucket["qty_sum"] += qty
        bucket["lot_count"] += 1
        if len(item_name) > len(str(bucket["item_name"])):
            bucket["item_name"] = item_name

    aggregated: List[_AggregatedHoldingLot] = []
    for bucket in buckets.values():
        qty_sum = int(bucket["qty_sum"])
        if qty_sum <= 0:
            continue
        avg_price = float(bucket["cost_sum"]) / qty_sum
        if avg_price <= 0:
            continue
        aggregated.append(
            _AggregatedHoldingLot(
                good_id=int(bucket["good_id"]),
                platform=str(bucket["platform"]),
                item_name=str(bucket["item_name"]),
                avg_purchase_price=round(avg_price, 4),
                total_quantity=qty_sum,
                lot_count=int(bucket["lot_count"]),
            )
        )

    aggregated.sort(key=lambda lot: (lot.platform, lot.good_id))
    return aggregated


def active_cs_item_lots(rows: List[Any]) -> Set[Tuple[int, str]]:
    """Return (good_id, platform) pairs that still exist in holdings inventory."""
    lots: Set[Tuple[int, str]] = set()
    for row in rows:
        good_id = getattr(row, "good_id", None)
        if good_id is None:
            continue
        try:
            gid = int(good_id)
        except (TypeError, ValueError):
            continue
        if gid <= 0:
            continue
        platform = str(getattr(row, "platform", None) or "yyyp").strip().lower() or "yyyp"
        lots.add((gid, platform))
    return lots


def _is_orphan_cs_item_price_rule(
    row: Any,
    active_lots: Set[Tuple[int, str]],
    active_good_ids: Set[int],
) -> bool:
    if str(getattr(row, "target_scope", "") or "") != "cs_item":
        return False
    if str(getattr(row, "alert_type", "") or "") != "cs_price_cross":
        return False
    try:
        good_id = int(str(getattr(row, "target", "") or "").strip())
    except (TypeError, ValueError):
        return False
    if good_id <= 0:
        return False

    params = _load_json_dict(getattr(row, "parameters", None))
    platform = str(params.get("platform") or "").strip().lower()
    if platform:
        return (good_id, platform) not in active_lots
    return good_id not in active_good_ids


def _load_json_dict(raw: Any) -> Dict[str, Any]:
    if raw is None or raw == "":
        return {}
    if isinstance(raw, dict):
        return raw
    try:
        loaded = json.loads(str(raw))
    except (TypeError, json.JSONDecodeError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def maybe_sync_cs_auto_alerts() -> None:
    """Fail-open hook for holdings mutations and app startup."""
    try:
        service = CSAutoAlertsService()
        if service.is_enabled():
            service.sync()
    except Exception as exc:
        logger.warning("[CSAutoAlerts] sync skipped: %s", exc)
