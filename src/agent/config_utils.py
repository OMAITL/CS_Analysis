# -*- coding: utf-8 -*-
"""Small config coercion helpers shared by CS agent entrypoints."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def coerce_config_int(raw_value: object, default: int, *, field_name: str | None = None) -> int:
    try:
        return int(raw_value)
    except (TypeError, ValueError, OverflowError):
        if field_name:
            logger.warning(
                "[AgentConfig] Invalid value for %s: %r, fallback to default %s",
                field_name,
                raw_value,
                default,
            )
        return default
