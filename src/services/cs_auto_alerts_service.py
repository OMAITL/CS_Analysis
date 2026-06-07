# -*- coding: utf-8 -*-
"""Auto-sync CS holdings alert rules from portfolio state."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from src.config import Config, get_config
from src.repositories.alert_repo import AlertRepository
from src.repositories.cs_holdings_repo import CSHoldingsRepository
from src.services.alert_service import AlertService


logger = logging.getLogger(__name__)

CS_AUTO_ALERT_SOURCE = "cs_auto"
CS_AUTO_NAME_PREFIX = "cs_auto:"


@dataclass(frozen=True)
class _AutoRuleSpec:
    name: str
    target_scope: str
    target: str
    alert_type: str
    parameters: Dict[str, Any]
    display_name: str
    severity: str = "warning"


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
        if not self.is_enabled():
            return stats

        expected = self._build_expected_rules()
        expected_keys = {self._rule_key(spec): spec for spec in expected}
        existing_rows, _ = self.alert_repo.list_rules(
            source=CS_AUTO_ALERT_SOURCE,
            page=1,
            page_size=1000,
        )
        existing_by_key: Dict[Tuple[str, str, str, str], Any] = {}
        for row in existing_rows:
            existing_by_key[self._row_key(row)] = row

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

        for row in existing_rows:
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
        for row in rows:
            good_id = getattr(row, "good_id", None)
            purchase_price = float(getattr(row, "purchase_price", 0.0) or 0.0)
            if good_id is None or purchase_price <= 0:
                continue
            platform = str(getattr(row, "platform", None) or "yyyp").lower()
            item_name = str(getattr(row, "item_name", "") or good_id)
            holding_id = int(getattr(row, "id", 0) or 0)
            if holding_id <= 0:
                continue

            if take_profit_pct > 0:
                tp_price = round(purchase_price * (1.0 + take_profit_pct / 100.0), 2)
                specs.append(
                    _AutoRuleSpec(
                        name=f"{CS_AUTO_NAME_PREFIX}holding:{holding_id}:take_profit",
                        target_scope="cs_item",
                        target=str(int(good_id)),
                        alert_type="cs_price_cross",
                        parameters={"direction": "above", "price": tp_price, "platform": platform},
                        display_name=f"CS 自动止盈 · {item_name} ≥ {tp_price}",
                    )
                )
            if stop_loss_pct > 0:
                sl_price = round(purchase_price * (1.0 - stop_loss_pct / 100.0), 2)
                if sl_price > 0:
                    specs.append(
                        _AutoRuleSpec(
                            name=f"{CS_AUTO_NAME_PREFIX}holding:{holding_id}:stop_loss",
                            target_scope="cs_item",
                            target=str(int(good_id)),
                            alert_type="cs_price_cross",
                            parameters={"direction": "below", "price": sl_price, "platform": platform},
                            display_name=f"CS 自动止损 · {item_name} ≤ {sl_price}",
                            severity="critical",
                        )
                    )
        return specs

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
