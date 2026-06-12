# -*- coding: utf-8 -*-
"""Tests for CS batched alert notifications."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.config import Config
from src.services.alert_worker import RuntimeAlertRule
from src.services.cs_alert_notification import (
    AlertNotificationItem,
    build_alert_markdown,
    build_alert_subject,
    normalize_alert_item,
    send_batched_alert_notification,
)
from src.services.cs_alerts import CSHoldingsAlert


class CSAlertNotificationTestCase(unittest.TestCase):
    def _config(self) -> Config:
        return Config()

    def test_normalize_cs_item_take_profit(self) -> None:
        rule = CSHoldingsAlert(
            target_scope="cs_item",
            target="770",
            alert_type="cs_price_cross",
            parameters={"direction": "above", "price": 558.77, "platform": "yyyp"},
            description="CS 自动止盈 · 格洛克18型 ≥ 558.77",
            metadata={"display_target": "饰品 770", "effective_target": "cs_item:770"},
        )
        runtime = RuntimeAlertRule(
            key="k1",
            rule=rule,
            source="db",
            display_target="饰品 770",
            effective_target="cs_item:770",
        )
        result = {
            "observed_value": 799.9,
            "threshold": 558.77,
            "reason": "CS item 770 price 799.90 above 558.77",
            "data_source": "csqaq",
            "diagnostics": {"good_id": 770, "platform": "yyyp", "direction": "above"},
        }
        with patch(
            "src.services.cs_alert_notification._lookup_holding_by_good_id",
            return_value={
                "item_name": "格洛克18型 | 核子花园",
                "pnl_pct": 71.8,
                "purchase_price": 465.64,
            },
        ):
            item = normalize_alert_item(runtime, result)

        self.assertTrue(item.is_cs)
        self.assertEqual(item.action_label, "止盈")
        self.assertEqual(item.item_name, "格洛克18型 | 核子花园")
        self.assertAlmostEqual(item.pnl_pct or 0.0, 71.8)

    def test_build_alert_subject_single_and_batch(self) -> None:
        config = self._config()
        single = [
            AlertNotificationItem(
                display_target="饰品 770",
                effective_target="cs_item:770",
                rule_name="止盈",
                alert_type="cs_price_cross",
                target_scope="cs_item",
                reason="triggered",
                item_name="格洛克18型",
                action_label="止盈",
                is_cs=True,
            )
        ]
        self.assertIn("格洛克18型", build_alert_subject(single, config))
        self.assertIn("止盈", build_alert_subject(single, config))

        batch = single + [
            AlertNotificationItem(
                display_target="全部 CS 持仓",
                effective_target="cs_holdings:all",
                rule_name="集中度",
                alert_type="cs_concentration",
                target_scope="cs_holdings",
                reason="concentration",
                action_label="集中度",
                is_cs=True,
            )
        ]
        self.assertIn("2 条触发", build_alert_subject(batch, config))

    def test_build_alert_markdown_includes_sections(self) -> None:
        items = [
            AlertNotificationItem(
                display_target="饰品 770",
                effective_target="cs_item:770",
                rule_name="CS 自动止盈",
                alert_type="cs_price_cross",
                target_scope="cs_item",
                reason="price above threshold",
                observed_value=799.9,
                threshold=558.77,
                item_name="格洛克18型",
                action_label="止盈",
                is_cs=True,
            )
        ]
        body = build_alert_markdown(items, ai_summary="建议关注止盈机会。")
        self.assertIn("AI 解读", body)
        self.assertIn("格洛克18型", body)
        self.assertIn("止盈", body)
        self.assertIn("799.9", body)
        self.assertNotIn("相关持仓", body)

    def test_build_alert_markdown_dedupes_related_holdings(self) -> None:
        duplicate_rows = [
            {"good_id": 7369, "platform": "yyyp", "item_name": "摩托手套（★） | 清凉薄荷 (久经沙场)", "pnl_pct": -2.68},
            {"good_id": 7369, "platform": "yyyp", "item_name": "摩托手套（★） | 清凉薄荷 (久经沙场)", "pnl_pct": -3.1},
            {"good_id": 1239, "platform": "yyyp", "item_name": "M4A1消音版 | 闪回 (久经沙场)", "pnl_pct": -95.28},
        ]
        items = [
            AlertNotificationItem(
                display_target="全部 CS 持仓",
                effective_target="cs_holdings:all",
                rule_name="CS 自动止损监控",
                alert_type="cs_stop_loss",
                target_scope="cs_holdings",
                reason="stop-loss near",
                action_label="止损监控",
                diagnostics={"top_items": duplicate_rows},
                is_cs=True,
            )
        ]
        body = build_alert_markdown(items)
        self.assertIn("清凉薄荷", body)
        self.assertIn("2 笔", body)
        self.assertIn("M4A1消音版", body)
        self.assertEqual(body.count("清凉薄荷"), 1)

    def test_send_batched_alert_notification_passes_subject(self) -> None:
        rule = CSHoldingsAlert(
            target_scope="cs_holdings",
            target="all",
            alert_type="cs_concentration",
            parameters={},
            description="CS 自动集中度",
        )
        runtime = RuntimeAlertRule(
            key="k2",
            rule=rule,
            source="db",
            display_target="全部 CS 持仓",
            effective_target="cs_holdings:all",
        )
        entry = SimpleNamespace(
            runtime_rule=runtime,
            result={
                "observed_value": 42.06,
                "threshold": 35.0,
                "reason": "concentration top weight 42.06%",
                "diagnostics": {},
            },
        )
        notifier = MagicMock()
        notifier.send_with_results.return_value = SimpleNamespace(
            dispatched=True,
            success=True,
            status="sent",
            channel_results=[],
        )
        with patch("src.services.cs_alert_notification.generate_alert_ai_summary", return_value=None):
            send_batched_alert_notification([entry], notifier=notifier, config=self._config())

        notifier.send_with_results.assert_called_once()
        kwargs = notifier.send_with_results.call_args.kwargs
        self.assertEqual(kwargs.get("route_type"), "alert")
        self.assertTrue(kwargs.get("email_send_to_all"))
        self.assertIn("CS价格预警", kwargs.get("email_subject") or "")


if __name__ == "__main__":
    unittest.main()
