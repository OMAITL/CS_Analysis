# -*- coding: utf-8 -*-
"""CS holdings risk report: concentration, stop-loss, stale price, platform exposure."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from src.config import Config, get_config
from src.services.cs_holdings_service import CSHoldingsService


class CSHoldingsRiskService:
    def __init__(
        self,
        *,
        holdings_service: Optional[CSHoldingsService] = None,
        config: Optional[Config] = None,
    ):
        self.holdings_service = holdings_service or CSHoldingsService()
        self.config = config or get_config()

    def get_risk_report(
        self,
        *,
        platform: Optional[str] = None,
        refresh_prices: bool = True,
        as_of: Optional[date] = None,
    ) -> Dict[str, Any]:
        snapshot = self.holdings_service.get_snapshot(
            refresh_prices=refresh_prices,
            platform=platform,
        )
        items = self._filter_items(list(snapshot.get("items") or []), platform=platform)
        thresholds = {
            "concentration_alert_pct": float(
                getattr(self.config, "cs_holdings_risk_concentration_alert_pct", 35.0)
            ),
            "stop_loss_alert_pct": float(
                getattr(self.config, "cs_holdings_risk_stop_loss_alert_pct", 10.0)
            ),
            "stop_loss_near_ratio": float(
                getattr(self.config, "cs_holdings_risk_stop_loss_near_ratio", 0.8)
            ),
            "pnl_gain_alert_pct": float(
                getattr(self.config, "cs_holdings_risk_pnl_gain_alert_pct", 30.0)
            ),
        }

        return {
            "as_of": (as_of or date.today()).isoformat(),
            "platform": platform or "all",
            "summary": snapshot.get("summary") or {},
            "thresholds": thresholds,
            "concentration": self._build_concentration(items, thresholds["concentration_alert_pct"]),
            "stop_loss": self._build_stop_loss(items, thresholds),
            "price_stale": self._build_price_stale(items),
            "platform_exposure": self._build_platform_exposure(items),
            "top_gainers": self._top_by_pnl(items, reverse=True),
            "top_losers": self._top_by_pnl(items, reverse=False),
        }

    def _filter_items(
        self,
        items: List[Dict[str, Any]],
        *,
        platform: Optional[str],
    ) -> List[Dict[str, Any]]:
        plat = (platform or "").strip().lower()
        if not plat or plat == "all":
            return items
        return [row for row in items if str(row.get("platform") or "yyyp").lower() == plat]

    def _build_concentration(self, items: List[Dict[str, Any]], threshold_pct: float) -> Dict[str, Any]:
        total_mv = sum(float(row.get("market_total") or 0.0) for row in items)
        rows: List[Dict[str, Any]] = []
        for row in items:
            market_total = float(row.get("market_total") or 0.0)
            weight = (market_total / total_mv * 100.0) if total_mv > 0 else 0.0
            rows.append(
                {
                    "holding_id": row.get("id"),
                    "good_id": row.get("good_id"),
                    "item_name": row.get("item_name"),
                    "market_total": round(market_total, 2),
                    "weight_pct": round(weight, 4),
                    "is_alert": bool(weight >= threshold_pct),
                }
            )
        rows.sort(key=lambda item: item["market_total"], reverse=True)
        top_weight = rows[0]["weight_pct"] if rows else 0.0
        return {
            "total_market_value": round(total_mv, 2),
            "top_weight_pct": round(float(top_weight), 4),
            "alert": bool(top_weight >= threshold_pct),
            "top_positions": rows[:10],
        }

    def _build_stop_loss(self, items: List[Dict[str, Any]], thresholds: Dict[str, float]) -> Dict[str, Any]:
        stop_loss_pct = float(thresholds["stop_loss_alert_pct"])
        near_ratio = float(thresholds["stop_loss_near_ratio"])
        near_threshold = stop_loss_pct * near_ratio
        warnings: List[Dict[str, Any]] = []
        for row in items:
            pnl_pct = row.get("pnl_pct")
            if pnl_pct is None:
                continue
            try:
                loss_pct = max(0.0, -float(pnl_pct))
            except (TypeError, ValueError):
                continue
            if loss_pct < near_threshold:
                continue
            warnings.append(
                {
                    "holding_id": row.get("id"),
                    "good_id": row.get("good_id"),
                    "item_name": row.get("item_name"),
                    "pnl_pct": round(float(pnl_pct), 4),
                    "loss_pct": round(loss_pct, 4),
                    "near_threshold_pct": round(near_threshold, 4),
                    "is_triggered": bool(loss_pct >= stop_loss_pct),
                }
            )
        warnings.sort(key=lambda item: item["loss_pct"], reverse=True)
        return {
            "near_alert": len(warnings) > 0,
            "triggered_count": sum(1 for item in warnings if item["is_triggered"]),
            "near_count": len(warnings),
            "items": warnings[:20],
        }

    def _build_price_stale(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        affected: List[Dict[str, Any]] = []
        for row in items:
            if row.get("good_id") is None or row.get("market_price") is None:
                affected.append(
                    {
                        "holding_id": row.get("id"),
                        "good_id": row.get("good_id"),
                        "item_name": row.get("item_name"),
                        "missing_good_id": row.get("good_id") is None,
                        "missing_market_price": row.get("market_price") is None,
                    }
                )
        return {
            "alert": bool(affected),
            "affected_count": len(affected),
            "items": affected[:20],
        }

    def _build_platform_exposure(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        total_mv = sum(float(row.get("market_total") or 0.0) for row in items)
        by_platform: Dict[str, float] = {}
        for row in items:
            plat = str(row.get("platform") or "yyyp").lower()
            by_platform[plat] = by_platform.get(plat, 0.0) + float(row.get("market_total") or 0.0)
        rows = [
            {
                "platform": plat,
                "market_total": round(value, 2),
                "weight_pct": round((value / total_mv * 100.0) if total_mv > 0 else 0.0, 4),
            }
            for plat, value in by_platform.items()
        ]
        rows.sort(key=lambda item: item["market_total"], reverse=True)
        return {"total_market_value": round(total_mv, 2), "platforms": rows}

    def _top_by_pnl(self, items: List[Dict[str, Any]], *, reverse: bool) -> List[Dict[str, Any]]:
        rows = [row for row in items if row.get("pnl_pct") is not None]
        rows.sort(key=lambda row: float(row.get("pnl_pct") or 0.0), reverse=reverse)
        return [
            {
                "holding_id": row.get("id"),
                "good_id": row.get("good_id"),
                "item_name": row.get("item_name"),
                "pnl_pct": row.get("pnl_pct"),
                "pnl": row.get("pnl"),
            }
            for row in rows[:5]
        ]
