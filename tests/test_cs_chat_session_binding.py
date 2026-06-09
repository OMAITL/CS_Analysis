# -*- coding: utf-8 -*-
"""Tests for CS chat session item binding."""

from __future__ import annotations

import unittest

from src.services import cs_chat_session_binding as binding


class CSChatSessionBindingTestCase(unittest.TestCase):
    def test_infer_item_name_from_assistant_reply(self) -> None:
        text = "仓位配置建议 (基于 AK-47 | 传承 (久经沙场), 当前价格 ≈ 287元)"
        name = binding.infer_item_name_from_text(text)
        self.assertIsNotNone(name)
        self.assertIn("传承", name or "")

    def test_infer_binding_from_messages(self) -> None:
        messages = [
            {"role": "user", "content": "传承能买吗"},
            {
                "role": "assistant",
                "content": "建议轻仓 (基于 AK-47 | 传承 (久经沙场))",
            },
        ]
        inferred = binding.infer_binding_from_messages(messages)
        self.assertIsNotNone(inferred)
        self.assertIn("AK-47", inferred["item_name"])


if __name__ == "__main__":
    unittest.main()
