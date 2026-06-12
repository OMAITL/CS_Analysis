# -*- coding: utf-8 -*-
"""
===================================
API v1 Endpoints 模块初始化
===================================

职责：
1. 声明所有 endpoint 路由模块
"""

from api.v1.endpoints import (
    health,
    system_config,
    auth,
    usage,
    alerts,
    cs,
)

__all__ = [
    "health",
    "system_config",
    "auth",
    "usage",
    "alerts",
    "cs",
]
