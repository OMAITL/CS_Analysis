# -*- coding: utf-8 -*-
"""
===================================
API v1 Schemas 模块初始化
===================================

职责：
1. 导出所有 Pydantic 模型
"""

from api.v1.schemas.common import (
    RootResponse,
    HealthResponse,
    ErrorResponse,
    SuccessResponse,
)
from api.v1.schemas.system_config import (
    SystemConfigFieldSchema,
    SystemConfigCategorySchema,
    SystemConfigSchemaResponse,
    SystemConfigItem,
    SystemConfigResponse,
    ExportSystemConfigResponse,
    SystemConfigUpdateItem,
    UpdateSystemConfigRequest,
    UpdateSystemConfigResponse,
    ValidateSystemConfigRequest,
    ImportSystemConfigRequest,
    ConfigValidationIssue,
    ValidateSystemConfigResponse,
    LLMCapabilityCheck,
    LLMCapabilityCheckResult,
    TestLLMChannelRequest,
    TestLLMChannelResponse,
    SystemConfigValidationErrorResponse,
    SystemConfigConflictResponse,
)
from api.v1.schemas.alerts import (
    AlertDeleteResponse,
    AlertNotificationItem,
    AlertNotificationListResponse,
    AlertRuleCreateRequest,
    AlertRuleItem,
    AlertRuleListResponse,
    AlertRuleTestResponse,
    AlertRuleUpdateRequest,
    AlertTriggerItem,
    AlertTriggerListResponse,
)

__all__ = [
    "RootResponse",
    "HealthResponse",
    "ErrorResponse",
    "SuccessResponse",
    "SystemConfigFieldSchema",
    "SystemConfigCategorySchema",
    "SystemConfigSchemaResponse",
    "SystemConfigItem",
    "SystemConfigResponse",
    "ExportSystemConfigResponse",
    "SystemConfigUpdateItem",
    "UpdateSystemConfigRequest",
    "UpdateSystemConfigResponse",
    "ValidateSystemConfigRequest",
    "ImportSystemConfigRequest",
    "ConfigValidationIssue",
    "ValidateSystemConfigResponse",
    "LLMCapabilityCheck",
    "LLMCapabilityCheckResult",
    "TestLLMChannelRequest",
    "TestLLMChannelResponse",
    "SystemConfigValidationErrorResponse",
    "SystemConfigConflictResponse",
    "AlertDeleteResponse",
    "AlertNotificationItem",
    "AlertNotificationListResponse",
    "AlertRuleCreateRequest",
    "AlertRuleItem",
    "AlertRuleListResponse",
    "AlertRuleTestResponse",
    "AlertRuleUpdateRequest",
    "AlertTriggerItem",
    "AlertTriggerListResponse",
]
