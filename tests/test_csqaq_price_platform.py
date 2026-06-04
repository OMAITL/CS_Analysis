# -*- coding: utf-8 -*-
"""Tests for CSQAQ primary platform resolution."""

from __future__ import annotations

import pytest

from market_provider.csqaq.client import resolve_price_platform
from market_provider.csqaq.schemas import CSQAQPlatform


def test_resolve_price_platform_defaults_to_yyyp(monkeypatch):
    monkeypatch.delenv("CSQAQ_PRICE_PLATFORM", raising=False)
    assert resolve_price_platform() is CSQAQPlatform.YYYP


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("buff", CSQAQPlatform.BUFF),
        ("yyyp", CSQAQPlatform.YYYP),
        ("悠悠有品", CSQAQPlatform.YYYP),
        ("2", CSQAQPlatform.YYYP),
        ("steam", CSQAQPlatform.STEAM),
    ],
)
def test_resolve_price_platform_aliases(raw, expected):
    assert resolve_price_platform(raw) is expected


def test_resolve_price_platform_env_override(monkeypatch):
    monkeypatch.setenv("CSQAQ_PRICE_PLATFORM", "buff")
    assert resolve_price_platform() is CSQAQPlatform.BUFF


def test_resolve_price_platform_invalid():
    with pytest.raises(ValueError, match="Unknown CSQAQ price platform"):
        resolve_price_platform("unknown")
