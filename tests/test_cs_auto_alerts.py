# -*- coding: utf-8 -*-
"""Tests for CS auto alert sync."""

from __future__ import annotations

from types import SimpleNamespace

from src.services.cs_auto_alerts_service import (
    CSAutoAlertsService,
    _is_orphan_cs_item_price_rule,
    active_cs_item_lots,
    aggregate_holdings_for_price_alerts,
)


class _FakeHolding:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class _FakeHoldingsRepo:
    def list_all(self, *, platform=None):
        return [
            _FakeHolding(
                id=1,
                good_id=100,
                item_name="AK-47 | 红线",
                platform="yyyp",
                purchase_price=1000.0,
            )
        ]


class _FakeAlertRepo:
    def __init__(self):
        self.rules = []
        self._next_id = 1

    def list_rules(self, **kwargs):
        source = kwargs.get("source")
        cs_only = kwargs.get("cs_only")
        page = kwargs.get("page", 1)
        page_size = kwargs.get("page_size", 20)
        rows = list(self.rules)
        if source:
            rows = [row for row in rows if row.source == source]
        if cs_only:
            rows = [row for row in rows if row.target_scope in {"cs_holdings", "cs_item"}]
        total = len(rows)
        start = (page - 1) * page_size
        end = start + page_size
        return rows[start:end], total

    def update_rule(self, rule_id, fields):
        for row in self.rules:
            if row.id == rule_id:
                for key, value in fields.items():
                    setattr(row, key, value)
                return row
        return None

    def delete_rule(self, rule_id):
        before = len(self.rules)
        self.rules = [row for row in self.rules if row.id != rule_id]
        return len(self.rules) < before


class _FakeAlertService:
    def __init__(self, repo):
        self.repo = repo

    def create_rule(self, payload):
        row = SimpleNamespace(
            id=len(self.repo.rules) + 1,
            name=payload["name"],
            target_scope=payload["target_scope"],
            target=payload["target"],
            alert_type=payload["alert_type"],
            parameters=__import__("json").dumps(payload["parameters"], sort_keys=True),
            severity=payload["severity"],
            source=payload.get("source", "api"),
            updated_at=None,
        )
        self.repo.rules.append(row)
        return {"id": row.id}


def test_cs_auto_alerts_sync_creates_portfolio_and_price_rules():
    config = SimpleNamespace(
        cs_holdings_auto_alerts_enabled=True,
        cs_auto_portfolio_alerts_enabled=True,
        cs_auto_price_alerts_enabled=True,
        cs_auto_price_alert_take_profit_pct=20.0,
        cs_auto_price_alert_stop_loss_pct=10.0,
    )
    repo = _FakeAlertRepo()
    service = CSAutoAlertsService(
        holdings_repo=_FakeHoldingsRepo(),
        alert_service=_FakeAlertService(repo),
        alert_repo=repo,
        config=config,
    )
    stats = service.sync()
    assert stats["created"] == 5
    assert len(repo.rules) == 5
    alert_types = {row.alert_type for row in repo.rules}
    assert "cs_stop_loss" in alert_types
    assert "cs_price_cross" in alert_types


def test_cs_auto_alerts_sync_deletes_stale_rules():
    config = SimpleNamespace(
        cs_holdings_auto_alerts_enabled=True,
        cs_auto_portfolio_alerts_enabled=True,
        cs_auto_price_alerts_enabled=False,
    )
    repo = _FakeAlertRepo()
    repo.rules.append(
        SimpleNamespace(
            id=99,
            name="old",
            target_scope="cs_item",
            target="999",
            alert_type="cs_price_cross",
            parameters='{"direction":"above","price":1,"platform":"yyyp"}',
            severity="warning",
            source="cs_auto",
        )
    )
    service = CSAutoAlertsService(
        holdings_repo=_FakeHoldingsRepo(),
        alert_service=_FakeAlertService(repo),
        alert_repo=repo,
        config=config,
    )
    stats = service.sync()
    assert stats["deleted"] == 1
    assert all(row.id != 99 for row in repo.rules)


def test_aggregate_holdings_for_price_alerts_weighted_average():
    rows = [
        _FakeHolding(id=1, good_id=100, item_name="AK-47 | 红线", platform="yyyp", purchase_price=1000.0, quantity=1),
        _FakeHolding(id=2, good_id=100, item_name="AK-47 | 红线", platform="yyyp", purchase_price=2000.0, quantity=1),
        _FakeHolding(id=3, good_id=200, item_name="M4A1-S", platform="buff", purchase_price=500.0, quantity=2),
    ]
    lots = aggregate_holdings_for_price_alerts(rows)
    assert len(lots) == 2

    ak = next(lot for lot in lots if lot.good_id == 100)
    assert ak.platform == "yyyp"
    assert ak.avg_purchase_price == 1500.0
    assert ak.lot_count == 2
    assert ak.total_quantity == 2

    m4 = next(lot for lot in lots if lot.good_id == 200)
    assert m4.platform == "buff"
    assert m4.avg_purchase_price == 500.0
    assert m4.lot_count == 1
    assert m4.total_quantity == 2


class _DuplicateHoldingsRepo(_FakeHoldingsRepo):
    def list_all(self, *, platform=None):
        return [
            _FakeHolding(
                id=1,
                good_id=100,
                item_name="AK-47 | 红线",
                platform="yyyp",
                purchase_price=1000.0,
                quantity=1,
            ),
            _FakeHolding(
                id=2,
                good_id=100,
                item_name="AK-47 | 红线",
                platform="yyyp",
                purchase_price=2000.0,
                quantity=1,
            ),
        ]


def test_cs_auto_alerts_deduplicates_same_good_id_with_weighted_average():
    config = SimpleNamespace(
        cs_holdings_auto_alerts_enabled=True,
        cs_auto_portfolio_alerts_enabled=False,
        cs_auto_price_alerts_enabled=True,
        cs_auto_price_alert_take_profit_pct=20.0,
        cs_auto_price_alert_stop_loss_pct=10.0,
    )
    repo = _FakeAlertRepo()
    service = CSAutoAlertsService(
        holdings_repo=_DuplicateHoldingsRepo(),
        alert_service=_FakeAlertService(repo),
        alert_repo=repo,
        config=config,
    )
    stats = service.sync()
    assert stats["created"] == 2
    price_rules = [row for row in repo.rules if row.alert_type == "cs_price_cross"]
    assert len(price_rules) == 2
    params = [__import__("json").loads(row.parameters) for row in price_rules]
    above = next(item for item in params if item["direction"] == "above")
    below = next(item for item in params if item["direction"] == "below")
    assert above["price"] == 1800.0
    assert below["price"] == 1350.0


class _EmptyHoldingsRepo(_FakeHoldingsRepo):
    def list_all(self, *, platform=None):
        return []


def test_cleanup_orphan_cs_item_price_rules_deletes_manual_rules_without_holdings():
    config = SimpleNamespace(cs_holdings_auto_alerts_enabled=False)
    repo = _FakeAlertRepo()
    repo.rules.append(
        SimpleNamespace(
            id=11,
            name="手动止盈 · AK-47",
            target_scope="cs_item",
            target="100",
            alert_type="cs_price_cross",
            parameters='{"direction":"above","price":1200,"platform":"yyyp"}',
            severity="warning",
            source="api",
        )
    )
    service = CSAutoAlertsService(
        holdings_repo=_EmptyHoldingsRepo(),
        alert_service=_FakeAlertService(repo),
        alert_repo=repo,
        config=config,
    )
    deleted = service.cleanup_orphan_cs_item_price_rules()
    assert deleted == 1
    assert repo.rules == []


def test_cleanup_orphan_cs_item_price_rules_keeps_rules_for_existing_lot():
    config = SimpleNamespace(cs_holdings_auto_alerts_enabled=False)
    repo = _FakeAlertRepo()
    repo.rules.append(
        SimpleNamespace(
            id=12,
            name="手动止盈 · AK-47",
            target_scope="cs_item",
            target="100",
            alert_type="cs_price_cross",
            parameters='{"direction":"above","price":1200,"platform":"yyyp"}',
            severity="warning",
            source="api",
        )
    )
    service = CSAutoAlertsService(
        holdings_repo=_FakeHoldingsRepo(),
        alert_service=_FakeAlertService(repo),
        alert_repo=repo,
        config=config,
    )
    deleted = service.cleanup_orphan_cs_item_price_rules()
    assert deleted == 0
    assert len(repo.rules) == 1


def test_active_cs_item_lots_and_orphan_detection():
    rows = [
        _FakeHolding(id=1, good_id=100, platform="yyyp"),
        _FakeHolding(id=2, good_id=200, platform="buff"),
    ]
    lots = active_cs_item_lots(rows)
    assert lots == {(100, "yyyp"), (200, "buff")}

    rule = SimpleNamespace(
        target_scope="cs_item",
        target="100",
        alert_type="cs_price_cross",
        parameters='{"direction":"below","price":900,"platform":"buff"}',
    )
    assert _is_orphan_cs_item_price_rule(rule, lots, {100, 200}) is True


def test_cs_auto_alerts_prunes_legacy_api_source_duplicates():
    config = SimpleNamespace(
        cs_holdings_auto_alerts_enabled=True,
        cs_auto_portfolio_alerts_enabled=True,
        cs_auto_price_alerts_enabled=False,
    )
    repo = _FakeAlertRepo()
    for idx in range(3):
        repo.rules.append(
            SimpleNamespace(
                id=idx + 1,
                name="CS 自动止损监控",
                target_scope="cs_holdings",
                target="all",
                alert_type="cs_stop_loss",
                parameters='{"mode":"near"}',
                severity="warning",
                source="api",
            )
        )
    service = CSAutoAlertsService(
        holdings_repo=_FakeHoldingsRepo(),
        alert_service=_FakeAlertService(repo),
        alert_repo=repo,
        config=config,
    )
    stats = service.sync()
    assert stats["deleted"] >= 2
    stop_loss_rules = [row for row in repo.rules if row.alert_type == "cs_stop_loss"]
    assert len(stop_loss_rules) == 1
