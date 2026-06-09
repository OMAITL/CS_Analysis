# -*- coding: utf-8 -*-
"""Tests for CS rank leader fetch helpers."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from src.services.cs_skill_prompt import fetch_cs_rank_leaders


class CSRankLeadersTestCase(unittest.TestCase):
    def test_fetch_cs_rank_leaders_browser_fallback(self) -> None:
        mock_client = MagicMock()
        mock_client.get_rank_list.side_effect = TimeoutError("api timeout")
        browser_rows = {
            "day_type": 7,
            "limit": 2,
            "gainers": [
                {
                    "good_id": 1,
                    "name": "法玛斯 | 雅典娜之眼",
                    "price": 100.0,
                    "change_pct": 12.5,
                }
            ],
            "losers": [
                {
                    "good_id": 2,
                    "name": "某饰品",
                    "price": 50.0,
                    "change_pct": -8.2,
                }
            ],
            "source": "browser_rank_page",
        }

        with patch("market_provider.csqaq.client.CSQAQClient", return_value=mock_client), \
             patch(
                 "src.services.cs_skill_prompt._fetch_cs_rank_leaders_via_browser",
                 return_value=browser_rows,
             ):
            payload = fetch_cs_rank_leaders(day_type=7, limit=2)

        self.assertEqual(payload["source"], "browser_rank_page")
        self.assertEqual(len(payload["gainers"]), 1)
        self.assertEqual(payload["gainers"][0]["name"], "法玛斯 | 雅典娜之眼")
        self.assertEqual(payload["gainers"][0]["change_pct"], 12.5)
        self.assertEqual(payload["losers"][0]["change_pct"], -8.2)


if __name__ == "__main__":
    unittest.main()
