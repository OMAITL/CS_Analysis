# -*- coding: utf-8 -*-
"""
===================================
数据访问层模块初始化
===================================

职责：
1. 导出 Repository 类（按子模块直接导入）
"""

from src.repositories.alert_repo import AlertRepository

__all__ = [
    "AlertRepository",
]
