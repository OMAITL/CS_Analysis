# -*- coding: utf-8 -*-
"""Tests for CS holdings alert evaluation."""

from __future__ import annotations

from src.services.cs_alerts import (
    CSHoldingsAlert,
    evaluate_cs_holdings_alert,
    normalize_cs_alert_parameters,
    normalize_cs_target,
)
from src.services.alert_service import AlertService


class _FakeRiskService:
    def get_risk_report(self, *, platform=None, refresh_prices=True, as_of=None):
        return {
            "as_of": "2026-06-08",
            "platform": platform or "all",
            "thresholds": {
                "concentration_alert_pct": 35.0,
                "stop_loss_alert_pct": 10.0,
                "stop_loss_near_ratio": 0.8,
            },
            "concentration": {"alert": True, "top_weight_pct": 42.0, "top_positions": []},
            "stop_loss": {
                "near_alert": True,
                "near_count": 1,
                "triggered_count": 1,
                "items": [{"item_name": "AK", "loss_pct": 12.0, "is_triggered": True}],
            },
            "price_stale": {
                "alert": True,
                "affected_count": 1,
                "items": [{"item_name": "Unknown", "missing_good_id": True}],
            },
        }


class _FakeHoldingsService:
    def get_snapshot(self, *, refresh_prices=True, platform=None, **kwargs):
        return {
            "items": [
                {"id": 1, "good_id": 100, "item_name": "AK", "pnl_pct": -15.0},
                {"id": 2, "good_id": 200, "item_name": "AWP", "pnl_pct": 20.0},
            ]
        }


def test_normalize_cs_alert_parameters():
    params = normalize_cs_alert_parameters(
        "cs_price_cross",
        {"direction": "below", "price": 100.0, "platform": "buff"},
    )
    assert params == {"direction": "below", "price": 100.0, "platform": "buff"}


def test_normalize_cs_target():
    assert normalize_cs_target("cs_holdings", "all") == "all"
    assert normalize_cs_target("cs_item", "12345") == "12345"


def test_evaluate_cs_concentration_alert():
    rule = CSHoldingsAlert(
        target_scope="cs_holdings",
        target="all",
        alert_type="cs_concentration",
        parameters={},
        metadata={"persisted_rule_id": 1},
    )
    result = evaluate_cs_holdings_alert(rule, risk_service=_FakeRiskService())
    assert result["triggered"] is True
    assert result["observed_value"] == 42.0


def test_evaluate_cs_pnl_threshold_loss():
    rule = CSHoldingsAlert(
        target_scope="cs_holdings",
        target="all",
        alert_type="cs_pnl_threshold",
        parameters={"direction": "loss", "threshold_pct": 10.0},
        metadata={"persisted_rule_id": 2},
    )
    result = evaluate_cs_holdings_alert(rule, holdings_service=_FakeHoldingsService())
    assert result["triggered"] is True
    assert result["observed_value"] == 15.0


def test_alert_service_accepts_cs_holdings_rule():
    service = AlertService()
    fields = service._normalize_rule_payload(
        {
            "target_scope": "cs_holdings",
            "target": "all",
            "alert_type": "cs_stop_loss",
            "parameters": {"mode": "near"},
            "severity": "warning",
        }
    )
    assert fields["target_scope"] == "cs_holdings"
    assert fields["alert_type"] == "cs_stop_loss"


def test_alert_service_create_rule_preserves_source():
    service = AlertService()
    fields = service._normalize_rule_payload(
        {
            "target_scope": "cs_holdings",
            "target": "all",
            "alert_type": "cs_stop_loss",
            "parameters": {"mode": "near"},
            "source": "cs_auto",
        },
        source="cs_auto",
    )
    assert fields["source"] == "cs_auto"


def test_evaluate_cs_item_price_cross_not_triggered_omits_record_status(monkeypatch):
    def _snapshot(_client, _good_id):
        return {"yyyp_sell_price": 658.43}

    monkeypatch.setattr("src.services.cs_alerts.CSQAQClient", lambda: object())
    monkeypatch.setattr("src.services.cs_alerts.fetch_item_snapshot", _snapshot)

    rule = CSHoldingsAlert(
        target_scope="cs_item",
        target="770",
        alert_type="cs_price_cross",
        parameters={"direction": "below", "price": 600.0, "platform": "yyyp"},
        metadata={"persisted_rule_id": 99},
    )
    result = evaluate_cs_holdings_alert(rule)
    assert result["triggered"] is False
    assert result["status"] == "not_triggered"
    assert result.get("record_status") is None


def test_evaluate_price_cross_falls_back_to_cached_holdings_price(monkeypatch):
    class _HoldingsWithCache(_FakeHoldingsService):
        def get_snapshot(self, *, refresh_prices=True, platform=None, **kwargs):
            return {
                "items": [
                    {
                        "good_id": 770,
                        "platform": "yyyp",
                        "market_price": 658.43,
                        "item_name": "Tec-9",
                    },
                ],
            }

    def _raise_unauthorized(*_args, **_kwargs):
        raise RuntimeError("401 Client Error: Unauthorized for url: https://api.csqaq.com/api/v1/info/good?id=770")

    monkeypatch.setattr("src.services.cs_alerts.fetch_item_snapshot", _raise_unauthorized)
    rule = CSHoldingsAlert(
        target_scope="cs_item",
        target="770",
        alert_type="cs_price_cross",
        parameters={"direction": "below", "price": 700.0, "platform": "yyyp"},
        metadata={"persisted_rule_id": 99},
    )
    result = evaluate_cs_holdings_alert(rule, holdings_service=_HoldingsWithCache())
    assert result["record_status"] == "degraded"
    assert result["observed_value"] == 658.43
    assert "cached price" in result["message"]
