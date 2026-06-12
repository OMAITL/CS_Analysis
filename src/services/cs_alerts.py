# -*- coding: utf-8 -*-
"""CS holdings alert helpers for Alert Center."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Optional, Sequence, Tuple

from market_provider.csqaq.client import CSQAQClient
from market_provider.csqaq.item_analysis import fetch_item_snapshot
from src.services.cs_holdings_risk_service import CSHoldingsRiskService
from src.services.cs_holdings_service import CSHoldingsService, _pick_market_price
from src.services.alert_runtime import RuntimeAlertPayload


CS_HOLDINGS_TARGET_SCOPES = frozenset({"cs_holdings", "cs_item"})
CS_HOLDINGS_ALERT_TYPES = frozenset({
    "cs_price_cross",
    "cs_pnl_threshold",
    "cs_price_stale",
    "cs_concentration",
    "cs_stop_loss",
})
CS_VALID_PLATFORMS = frozenset({"all", "yyyp", "buff", "steam"})
EXPANDED_CS_ITEM_SOFT_CAP = 100


def _safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def dedupe_cs_holding_top_items(
    rows: Sequence[Any],
    *,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """Merge duplicate good_id/platform rows (multiple lots) for alert display."""
    buckets: Dict[Tuple[int, str], Dict[str, Any]] = {}
    order: List[Tuple[int, str]] = []
    for raw in rows:
        if not isinstance(raw, dict):
            continue
        good_id = raw.get("good_id")
        if good_id is None:
            continue
        try:
            gid = int(good_id)
        except (TypeError, ValueError):
            continue
        platform = str(raw.get("platform") or "yyyp").lower()
        key = (gid, platform)
        item_name = str(raw.get("item_name") or gid).strip() or str(gid)
        if key not in buckets:
            buckets[key] = {
                **raw,
                "good_id": gid,
                "platform": platform,
                "item_name": item_name,
                "lot_count": 1,
            }
            order.append(key)
            continue
        bucket = buckets[key]
        bucket["lot_count"] = int(bucket.get("lot_count") or 1) + 1
        if len(item_name) > len(str(bucket.get("item_name") or "")):
            bucket["item_name"] = item_name
        new_pnl = _safe_float(raw.get("pnl_pct"))
        old_pnl = _safe_float(bucket.get("pnl_pct"))
        if new_pnl is not None and (old_pnl is None or new_pnl < old_pnl):
            bucket["pnl_pct"] = new_pnl
        new_loss = _safe_float(raw.get("loss_pct"))
        old_loss = _safe_float(bucket.get("loss_pct"))
        if new_loss is not None and (old_loss is None or new_loss > old_loss):
            bucket["loss_pct"] = new_loss

    output: List[Dict[str, Any]] = []
    for key in order:
        row = dict(buckets[key])
        lot_count = int(row.pop("lot_count", 1) or 1)
        if lot_count > 1:
            row["item_name"] = f"{row['item_name']}（{lot_count} 笔）"
        output.append(row)
        if len(output) >= max(1, int(limit)):
            break
    return output


@dataclass
class CSHoldingsAlert:
    """Runtime alert for CS holdings / item rules."""

    target_scope: str
    target: str
    alert_type: str
    parameters: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    stock_code: str = ""

    def __post_init__(self) -> None:
        effective_target = self.metadata.get("effective_target") or cs_effective_target(
            self.target_scope,
            self.target,
        )
        self.stock_code = str(effective_target)


def normalize_cs_alert_parameters(alert_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    if alert_type not in CS_HOLDINGS_ALERT_TYPES:
        raise ValueError(f"unsupported cs alert_type: {alert_type}")
    if not isinstance(parameters, dict):
        raise ValueError("parameters must be an object")

    if alert_type == "cs_price_cross":
        direction = str(parameters.get("direction") or "above").strip().lower()
        if direction not in {"above", "below"}:
            raise ValueError("cs_price_cross direction must be above or below")
        price = float(parameters.get("price") or 0)
        if price <= 0:
            raise ValueError("cs_price_cross price must be > 0")
        platform = str(parameters.get("platform") or "yyyp").strip().lower()
        if platform not in {"yyyp", "buff", "steam"}:
            raise ValueError("cs_price_cross platform must be yyyp, buff, or steam")
        return {"direction": direction, "price": price, "platform": platform}

    if alert_type == "cs_pnl_threshold":
        direction = str(parameters.get("direction") or "loss").strip().lower()
        if direction not in {"loss", "gain"}:
            raise ValueError("cs_pnl_threshold direction must be loss or gain")
        threshold_pct = float(parameters.get("threshold_pct") or 10.0)
        if threshold_pct <= 0:
            raise ValueError("cs_pnl_threshold threshold_pct must be > 0")
        return {"direction": direction, "threshold_pct": threshold_pct}

    if alert_type == "cs_stop_loss":
        mode = str(parameters.get("mode") or "near").strip().lower()
        if mode not in {"near", "breach"}:
            raise ValueError("cs_stop_loss mode must be near or breach")
        return {"mode": mode}

    return {}


def cs_effective_target(target_scope: str, target: str) -> str:
    target_text = str(target or "all").strip() or "all"
    if target_scope == "cs_item":
        return f"cs_item:{target_text}"
    return f"cs_holdings:{target_text}"


def cs_display_target(target_scope: str, target: str) -> str:
    target_text = str(target or "all").strip() or "all"
    if target_scope == "cs_item":
        return f"饰品 {target_text}"
    if target_text == "all":
        return "全部 CS 持仓"
    return f"CS 持仓 ({target_text})"


def normalize_cs_target(target_scope: str, target: str) -> str:
    target_text = str(target or "").strip()
    if target_scope == "cs_item":
        try:
            good_id = int(target_text)
        except (TypeError, ValueError) as exc:
            raise ValueError("cs_item target must be a positive good_id") from exc
        if good_id <= 0:
            raise ValueError("cs_item target must be a positive good_id")
        return str(good_id)
    normalized = (target_text or "all").lower()
    if normalized not in CS_VALID_PLATFORMS:
        raise ValueError("cs_holdings target must be all, yyyp, buff, or steam")
    return normalized


def make_cs_holdings_payload(*, parent_key: str, data: Dict[str, Any]) -> RuntimeAlertPayload:
    effective_target = cs_effective_target(data["target_scope"], data["target"])
    display_target = cs_display_target(data["target_scope"], data["target"])
    rule = CSHoldingsAlert(
        target_scope=data["target_scope"],
        target=data["target"],
        alert_type=data["alert_type"],
        parameters=dict(data.get("parameters") or {}),
        metadata={
            "persisted_rule_id": data["id"],
            "effective_target": effective_target,
            "display_target": display_target,
        },
        description=data.get("name") or data["alert_type"],
    )
    return RuntimeAlertPayload(
        key=f"{parent_key}|{effective_target}",
        rule=rule,
        effective_target=effective_target,
        display_target=display_target,
    )


def expand_cs_item_targets(
    *,
    target_scope: str,
    target: str,
    holdings_service: Optional[CSHoldingsService] = None,
) -> Tuple[List[Dict[str, Any]], int]:
    """Expand cs_holdings batch rules into per-good_id targets for item-level alerts."""

    if target_scope != "cs_holdings":
        return [], 0
    service = holdings_service or CSHoldingsService()
    platform = None if target in {"", "all"} else target
    snapshot = service.get_snapshot(refresh_prices=False, platform=platform)
    seen: set[int] = set()
    rows: List[Dict[str, Any]] = []
    overflow = 0
    for item in snapshot.get("items") or []:
        good_id = item.get("good_id")
        if good_id is None:
            continue
        try:
            gid = int(good_id)
        except (TypeError, ValueError):
            continue
        if gid in seen:
            continue
        seen.add(gid)
        if len(rows) >= EXPANDED_CS_ITEM_SOFT_CAP:
            overflow += 1
            continue
        rows.append(
            {
                "good_id": gid,
                "item_name": item.get("item_name") or str(gid),
                "platform": item.get("platform") or "yyyp",
            }
        )
    return rows, overflow


def evaluate_cs_holdings_alert(
    rule: CSHoldingsAlert,
    *,
    holdings_service: Optional[CSHoldingsService] = None,
    risk_service: Optional[CSHoldingsRiskService] = None,
) -> Dict[str, Any]:
    if rule.alert_type == "cs_price_cross":
        return _evaluate_price_cross(rule, holdings_service=holdings_service)
    if rule.alert_type == "cs_pnl_threshold":
        return _evaluate_pnl_threshold(rule, holdings_service=holdings_service)

    platform = None if rule.target in {"", "all"} else rule.target
    risk = risk_service or CSHoldingsRiskService(holdings_service=holdings_service)
    report = risk.get_risk_report(platform=platform, refresh_prices=True)

    if rule.alert_type == "cs_price_stale":
        return _evaluate_price_stale(rule, report)
    if rule.alert_type == "cs_stop_loss":
        return _evaluate_stop_loss(rule, report)
    if rule.alert_type == "cs_concentration":
        return _evaluate_concentration(rule, report)

    return _cs_result(
        rule,
        triggered=False,
        observed_value=None,
        threshold=None,
        message=f"unsupported cs alert_type: {rule.alert_type}",
        record_status="failed",
        diagnostics={"error": "unsupported_cs_alert_type"},
    )


def _format_price_fetch_error(exc: Exception) -> str:
    text = str(exc)
    if "401" in text and "Unauthorized" in text:
        return (
            "CSQAQ 鉴权失败(401)：请检查 .env 中 CSQAQ_API_TOKEN，"
            "并在 CSQAQ 用户中心将当前公网 IP 加入白名单后重启后端"
        )
    return f"price fetch failed: {exc}"


def _lookup_cached_holdings_price(
    good_id: int,
    platform: str,
    holdings_service: Optional[CSHoldingsService],
) -> Optional[float]:
    service = holdings_service or CSHoldingsService()
    snapshot = service.get_snapshot(refresh_prices=False)
    for item in snapshot.get("items") or []:
        try:
            gid = int(item.get("good_id"))
        except (TypeError, ValueError):
            continue
        if gid != good_id:
            continue
        item_platform = str(item.get("platform") or "yyyp").lower()
        if item_platform != platform.lower():
            continue
        market_price = item.get("market_price")
        if market_price is None:
            continue
        try:
            return float(market_price)
        except (TypeError, ValueError):
            continue
    return None


def _evaluate_price_cross(
    rule: CSHoldingsAlert,
    *,
    holdings_service: Optional[CSHoldingsService] = None,
) -> Dict[str, Any]:
    direction = str(rule.parameters.get("direction") or "above")
    threshold = float(rule.parameters.get("price") or 0)
    platform = str(rule.parameters.get("platform") or "yyyp")
    try:
        good_id = int(rule.target)
    except (TypeError, ValueError):
        return _cs_result(
            rule,
            triggered=False,
            observed_value=None,
            threshold=threshold,
            message="invalid cs_item good_id target",
            record_status="failed",
        )

    price_source = "csqaq"
    fetch_error: Optional[str] = None
    observed: Optional[float] = None
    try:
        client = CSQAQClient()
        snapshot = fetch_item_snapshot(client, good_id)
        observed = _pick_market_price(snapshot, platform)
    except Exception as exc:
        fetch_error = str(exc)
        observed = _lookup_cached_holdings_price(good_id, platform, holdings_service)
        price_source = "holdings_cache"
        if observed is None:
            return _cs_result(
                rule,
                triggered=False,
                observed_value=None,
                threshold=threshold,
                message=_format_price_fetch_error(exc),
                record_status="failed",
                data_source="csqaq",
                diagnostics={"good_id": good_id, "platform": platform, "fetch_error": fetch_error},
            )

    if observed is None:
        return _cs_result(
            rule,
            triggered=False,
            observed_value=None,
            threshold=threshold,
            message=f"cs_item {good_id} price unavailable on {platform}",
            record_status="degraded",
            data_source=price_source,
        )

    triggered = observed >= threshold if direction == "above" else observed <= threshold
    message = (
        f"CS item {good_id} price {observed:.2f} {direction} {threshold:.2f}"
        if triggered
        else f"CS item {good_id} price {observed:.2f} not {direction} {threshold:.2f}"
    )
    if fetch_error:
        message = f"{message} (cached price; CSQAQ unavailable)"
    return _cs_result(
        rule,
        triggered=triggered,
        observed_value=float(observed),
        threshold=threshold,
        message=message,
        record_status="degraded" if fetch_error else None,
        data_source=price_source,
        diagnostics={
            "good_id": good_id,
            "platform": platform,
            "direction": direction,
            "price_source": price_source,
            **({"fetch_error": fetch_error} if fetch_error else {}),
        },
    )


def _evaluate_pnl_threshold(
    rule: CSHoldingsAlert,
    *,
    holdings_service: Optional[CSHoldingsService] = None,
) -> Dict[str, Any]:
    service = holdings_service or CSHoldingsService()
    platform = None if rule.target in {"", "all"} else rule.target
    direction = str(rule.parameters.get("direction") or "loss")
    threshold = float(rule.parameters.get("threshold_pct") or 10.0)
    snapshot = service.get_snapshot(refresh_prices=True, platform=platform)
    affected: List[Dict[str, Any]] = []
    for row in snapshot.get("items") or []:
        pnl_pct = row.get("pnl_pct")
        if pnl_pct is None:
            continue
        try:
            value = float(pnl_pct)
        except (TypeError, ValueError):
            continue
        if direction == "loss":
            if value <= -threshold:
                affected.append(
                    {
                        "holding_id": row.get("id"),
                        "good_id": row.get("good_id"),
                        "item_name": row.get("item_name"),
                        "pnl_pct": round(value, 4),
                    }
                )
        elif value >= threshold:
            affected.append(
                {
                    "holding_id": row.get("id"),
                    "good_id": row.get("good_id"),
                    "item_name": row.get("item_name"),
                    "pnl_pct": round(value, 4),
                }
            )

    observed = max((abs(float(item["pnl_pct"])) for item in affected), default=0.0)
    triggered = bool(affected)
    message = (
        f"CS holdings {direction} threshold {threshold:.2f}%: {len(affected)} items"
        if triggered
        else f"CS holdings {direction} threshold {threshold:.2f}%: no affected items"
    )
    return _cs_result(
        rule,
        triggered=triggered,
        observed_value=observed if triggered else 0.0,
        threshold=threshold,
        message=message,
        data_source="cs_holdings_snapshot",
        diagnostics={"direction": direction, "affected_count": len(affected), "top_items": dedupe_cs_holding_top_items(affected, limit=5)},
    )


def _evaluate_price_stale(rule: CSHoldingsAlert, report: Dict[str, Any]) -> Dict[str, Any]:
    stale = report.get("price_stale") or {}
    affected = list(stale.get("items") or [])
    observed = float(stale.get("affected_count") or 0)
    triggered = bool(stale.get("alert"))
    message = (
        f"{_display_scope(report)} stale or missing prices: {len(affected)} items"
        if triggered
        else f"{_display_scope(report)} prices are current"
    )
    return _cs_result(
        rule,
        triggered=triggered,
        observed_value=observed,
        threshold=0.0,
        message=message,
        data_source="cs_holdings_risk",
        diagnostics={"affected_count": len(affected), "top_items": dedupe_cs_holding_top_items(affected, limit=5)},
        data_timestamp=_parse_date(report.get("as_of")),
    )


def _evaluate_stop_loss(rule: CSHoldingsAlert, report: Dict[str, Any]) -> Dict[str, Any]:
    stop_loss = report.get("stop_loss") or {}
    mode = str(rule.parameters.get("mode") or "near")
    items = list(stop_loss.get("items") or [])
    if mode == "breach":
        affected = [item for item in items if bool(item.get("is_triggered"))]
        triggered = bool(affected)
    else:
        affected = items
        triggered = bool(stop_loss.get("near_alert")) and bool(affected)

    threshold_key = "stop_loss_alert_pct" if mode == "breach" else "stop_loss_near_ratio"
    threshold = _threshold(report, threshold_key)
    if mode == "near":
        stop_loss_pct = _threshold(report, "stop_loss_alert_pct") or 0.0
        near_ratio = _threshold(report, "stop_loss_near_ratio") or 0.0
        threshold = stop_loss_pct * near_ratio

    observed = max((float(item.get("loss_pct") or 0.0) for item in affected), default=0.0)
    message = (
        f"{_display_scope(report)} stop-loss {mode}: {len(affected)} items"
        if triggered
        else f"{_display_scope(report)} stop-loss {mode}: no affected items"
    )
    return _cs_result(
        rule,
        triggered=triggered,
        observed_value=observed,
        threshold=threshold,
        message=message,
        data_source="cs_holdings_risk",
        diagnostics={
            "mode": mode,
            "near_count": stop_loss.get("near_count", 0),
            "triggered_count": stop_loss.get("triggered_count", 0),
            "top_items": dedupe_cs_holding_top_items(affected, limit=5),
        },
        data_timestamp=_parse_date(report.get("as_of")),
    )


def _evaluate_concentration(rule: CSHoldingsAlert, report: Dict[str, Any]) -> Dict[str, Any]:
    concentration = report.get("concentration") or {}
    observed = float(concentration.get("top_weight_pct") or 0.0)
    threshold = _threshold(report, "concentration_alert_pct")
    triggered = bool(concentration.get("alert"))
    message = f"{_display_scope(report)} concentration top weight {observed:.2f}%"
    return _cs_result(
        rule,
        triggered=triggered,
        observed_value=observed,
        threshold=threshold,
        message=message,
        data_source="cs_holdings_risk",
        diagnostics={
            "total_market_value": concentration.get("total_market_value"),
            "top_weight_pct": observed,
            "top_positions": (concentration.get("top_positions") or [])[:5],
        },
        data_timestamp=_parse_date(report.get("as_of")),
    )


def _cs_result(
    rule: CSHoldingsAlert,
    *,
    triggered: bool,
    observed_value: Optional[float],
    threshold: Optional[float],
    message: str,
    record_status: Optional[str] = None,
    diagnostics: Optional[Dict[str, Any]] = None,
    data_source: Optional[str] = None,
    data_timestamp: Optional[Any] = None,
) -> Dict[str, Any]:
    if triggered and record_status is None:
        record_status = "triggered"
    return {
        "rule_id": int(rule.metadata.get("persisted_rule_id", 0) or 0),
        "status": "triggered" if triggered else "not_triggered",
        "record_status": record_status,
        "triggered": triggered,
        "observed_value": observed_value,
        "threshold": threshold,
        "data_source": data_source,
        "data_timestamp": data_timestamp.isoformat() if hasattr(data_timestamp, "isoformat") else data_timestamp,
        "reason": message,
        "message": message,
        "diagnostics": diagnostics or {},
    }


def _display_scope(report: Dict[str, Any]) -> str:
    platform = str(report.get("platform") or "all")
    return "全部 CS 持仓" if platform == "all" else f"CS 持仓 ({platform})"


def _threshold(report: Dict[str, Any], key: str) -> Optional[float]:
    thresholds = report.get("thresholds") or {}
    value = thresholds.get(key)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_date(value: Any) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None
