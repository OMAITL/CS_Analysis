# -*- coding: utf-8 -*-
"""Tests for CS daily report service."""

from __future__ import annotations

import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.config import Config
from src.services import cs_daily_report_service
from src.services.cs_daily_report_service import (
    _aggregate_holdings_for_report,
    _escape_md_table_cell,
    build_daily_subject,
    build_daily_template_markdown,
    maybe_run_cs_daily_report,
)


class CSDailyReportServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        cs_daily_report_service._last_sent_date = None

    def _config(self, **overrides) -> Config:
        config = Config()
        config.cs_daily_report_enabled = True
        config.cs_daily_report_time = "00:00"
        for key, value in overrides.items():
            setattr(config, key, value)
        return config

    def test_escape_md_table_cell_pipes(self) -> None:
        raw = "摩托手套 (★) | 清凉薄荷 (久经沙场)"
        escaped = _escape_md_table_cell(raw)
        self.assertIn("\\|", escaped)
        self.assertNotEqual(raw, escaped)

    def test_aggregate_holdings_merges_same_good_id(self) -> None:
        rows = [
            {
                "good_id": 101,
                "platform": "yyyp",
                "item_name": "摩托手套 (★) | 清凉薄荷 (久经沙场)",
                "quantity": 1,
                "purchase_price": 100.0,
                "market_price": 80.0,
                "market_total": 80.0,
            },
            {
                "good_id": 101,
                "platform": "yyyp",
                "item_name": "摩托手套 (★) | 清凉薄荷 (久经沙场)",
                "quantity": 1,
                "purchase_price": 200.0,
                "market_price": 80.0,
                "market_total": 80.0,
            },
        ]
        merged = _aggregate_holdings_for_report(rows)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["lot_count"], 2)
        self.assertEqual(merged[0]["market_total"], 160.0)

    def test_build_daily_template_markdown(self) -> None:
        context = {
            "report_date": "2026-06-09",
            "generated_at": "2026-06-09 20:05:00",
            "market": {
                "index_summary": {
                    "daily_pct_chg": 1.2,
                    "latest_close": 1234.5,
                    "chg_num": 12.3,
                    "open": 1200.0,
                    "high": 1250.0,
                    "low": 1190.0,
                },
                "home": {
                    "main_index": {
                        "id": 1,
                        "name": "饰品指数",
                        "market_index": 1234.5,
                        "chg_num": 12.3,
                        "chg_rate": 1.2,
                        "open": 1200.0,
                        "high": 1250.0,
                        "low": 1190.0,
                    }
                },
                "sub_indexes": [
                    {
                        "name": "租赁指数",
                        "market_index": 731.65,
                        "chg_rate": 1.63,
                    }
                ],
                "rank_leaders": {
                    "day_type": 7,
                    "gainers": [
                        {
                            "name": "法玛斯 | 雅典娜之眼",
                            "price": 100.0,
                            "change_pct": 69180.0,
                        }
                    ],
                    "losers": [
                        {
                            "name": "某饰品",
                            "price": 50.0,
                            "change_pct": -42.5,
                        }
                    ],
                },
            },
            "portfolio": {
                "summary": {
                    "item_count": 3,
                    "total_market_value": 10000.0,
                    "total_cost": 8000.0,
                    "total_pnl": 2000.0,
                }
            },
            "risk": {"concentration": {"top_weight_pct": 42.0}},
            "top_items": [
                {
                    "item_name": "格洛克18型 | 核子花园 (崭新出厂)",
                    "market_price": 799.9,
                    "pnl_pct": 71.8,
                    "trend_status": "偏多",
                }
            ],
            "rank_analysis": "涨幅榜多为低价小样本，**不宜追涨**；跌幅榜需关注流动性。",
        }
        body = build_daily_template_markdown(context, ai_summary="大盘**偏强**，注意**集中度**。")
        self.assertIn("CS 饰品每日复盘", body)
        self.assertIn("AI 总结", body)
        self.assertIn("格洛克18型", body)
        self.assertIn("**总市值**", body)
        self.assertIn("租赁指数", body)
        self.assertIn("涨幅榜 Top 5", body)
        self.assertIn("涨跌幅榜解读", body)
        self.assertNotIn("今日告警回顾", body)
        parts = [
            part.strip()
            for part in body.split("|")
            if "格洛克18型" in part
        ]
        self.assertTrue(parts, "expected top holdings row to stay in one table cell")

    def test_build_daily_subject(self) -> None:
        context = {
            "report_date": "2026-06-09",
            "portfolio": {"summary": {"total_pnl": 2000.0, "total_cost": 8000.0}},
        }
        subject = build_daily_subject(context, self._config())
        self.assertIn("2026-06-09", subject)
        self.assertIn("CS每日复盘", subject)

    def test_maybe_run_sends_once_per_day(self) -> None:
        notifier = MagicMock()
        notifier.send_with_results.return_value = SimpleNamespace(
            dispatched=True,
            success=True,
            status="sent",
            channel_results=[],
            message="ok",
        )
        config = self._config()
        now = datetime(2026, 6, 9, 20, 5, 0)

        with patch("src.services.cs_daily_report_service.collect_daily_context", return_value={"report_date": "2026-06-09", "portfolio": {"summary": {}}}), \
             patch("src.services.cs_daily_report_service.generate_daily_ai_summary", return_value=None), \
             patch("src.services.cs_daily_report_service.generate_rank_analysis", return_value=None):
            first = maybe_run_cs_daily_report(config=config, notifier=notifier, now=now)
            second = maybe_run_cs_daily_report(config=config, notifier=notifier, now=now)

        self.assertTrue(first)
        self.assertFalse(second)
        self.assertEqual(notifier.send_with_results.call_count, 1)


if __name__ == "__main__":
    unittest.main()
