# -*- coding: utf-8 -*-
"""Tests for CS holdings risk report."""

from __future__ import annotations

from types import SimpleNamespace

from src.services.cs_holdings_risk_service import CSHoldingsRiskService


class _FakeHoldingsService:
    def get_snapshot(self, *, refresh_prices=True, platform=None, **kwargs):
        items = [
            {
                "id": 1,
                "good_id": 100,
                "item_name": "AK-47 | 红线",
                "platform": "yyyp",
                "market_total": 700.0,
                "market_price": 700.0,
                "pnl_pct": -12.0,
            },
            {
                "id": 2,
                "good_id": 200,
                "item_name": "AWP | 二西莫夫",
                "platform": "buff",
                "market_total": 300.0,
                "market_price": 300.0,
                "pnl_pct": 5.0,
            },
            {
                "id": 3,
                "good_id": None,
                "item_name": "未匹配饰品",
                "platform": "yyyp",
                "market_total": 0.0,
                "market_price": None,
                "pnl_pct": None,
            },
        ]
        if platform and platform != "all":
            items = [row for row in items if row["platform"] == platform]
        return {
            "summary": {"item_count": len(items), "row_count": len(items), "total_market_value": 1000.0},
            "items": items,
        }


def test_cs_holdings_risk_concentration_and_stop_loss():
    config = SimpleNamespace(
        cs_holdings_risk_concentration_alert_pct=35.0,
        cs_holdings_risk_stop_loss_alert_pct=10.0,
        cs_holdings_risk_stop_loss_near_ratio=0.8,
        cs_holdings_risk_pnl_gain_alert_pct=30.0,
    )
    service = CSHoldingsRiskService(holdings_service=_FakeHoldingsService(), config=config)
    report = service.get_risk_report(refresh_prices=False)

    assert report["concentration"]["top_weight_pct"] == 70.0
    assert report["concentration"]["alert"] is True
    assert report["stop_loss"]["near_count"] == 1
    assert report["stop_loss"]["triggered_count"] == 1
    assert report["price_stale"]["affected_count"] == 1
    assert len(report["platform_exposure"]["platforms"]) == 2


def test_cs_holdings_risk_platform_filter():
    config = SimpleNamespace(
        cs_holdings_risk_concentration_alert_pct=35.0,
        cs_holdings_risk_stop_loss_alert_pct=10.0,
        cs_holdings_risk_stop_loss_near_ratio=0.8,
        cs_holdings_risk_pnl_gain_alert_pct=30.0,
    )
    service = CSHoldingsRiskService(holdings_service=_FakeHoldingsService(), config=config)
    report = service.get_risk_report(refresh_prices=False, platform="buff")

    assert report["platform"] == "buff"
    assert report["concentration"]["top_weight_pct"] == 100.0
    assert report["stop_loss"]["near_count"] == 0
