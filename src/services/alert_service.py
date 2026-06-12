# -*- coding: utf-8 -*-
"""CS holdings alert service for Alert API."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from src.repositories.alert_repo import AlertRepository
from src.services.alert_runtime import (
    DRY_RUN_TARGET_TIMEOUT_SECONDS,
    DRY_RUN_TOTAL_TIMEOUT_SECONDS,
    RuntimeAlertPayload,
    StaticAlertEvaluation,
    aggregate_dry_run_results,
    evaluate_static_alert,
    make_static_payload,
    result_to_target_result,
)
from src.services.cs_alerts import (
    CS_HOLDINGS_ALERT_TYPES,
    CS_HOLDINGS_TARGET_SCOPES,
    CSHoldingsAlert,
    cs_effective_target,
    evaluate_cs_holdings_alert,
    expand_cs_item_targets,
    make_cs_holdings_payload,
    normalize_cs_alert_parameters,
    normalize_cs_target,
)
from src.storage import (
    AlertCooldownRecord,
    AlertNotificationRecord,
    AlertRuleRecord,
    AlertTriggerRecord,
    DatabaseManager,
)
from src.utils.sanitize import sanitize_diagnostic_text

SUPPORTED_ALERT_TYPES = CS_HOLDINGS_ALERT_TYPES
SUPPORTED_TARGET_SCOPES = CS_HOLDINGS_TARGET_SCOPES
SUPPORTED_SEVERITIES = frozenset({"info", "warning", "critical"})
NULLABLE_RULE_UPDATE_FIELDS = frozenset({"cooldown_policy", "notification_policy"})

logger = logging.getLogger(__name__)


class AlertServiceError(ValueError):
    """Raised when alert service input is invalid."""

    error_code = "validation_error"


class AlertNotFoundError(AlertServiceError):
    """Raised when an alert resource does not exist."""

    error_code = "not_found"


class UnsupportedAlertTypeError(AlertServiceError):
    """Raised when the API receives a non-runtime alert type."""

    error_code = "unsupported_alert_type"


class AlertService:
    """Business logic for CS alert rule CRUD and dry-run evaluation."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager.get_instance()
        self.repo = AlertRepository(self.db)

    def create_rule(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        fields = self._normalize_rule_payload(payload, source=str(payload.get("source") or "api"))
        return self._serialize_rule(self.repo.create_rule(fields))

    def get_rule(self, rule_id: int) -> Dict[str, Any]:
        row = self.repo.get_rule(rule_id)
        if row is None:
            raise AlertNotFoundError(f"Alert rule not found: {rule_id}")
        return self._serialize_rule(row)

    def update_rule(self, rule_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        row = self.repo.get_rule(rule_id)
        if row is None:
            raise AlertNotFoundError(f"Alert rule not found: {rule_id}")
        if not payload:
            raise AlertServiceError("No fields provided for update")
        self._validate_rule_update_payload(payload)

        merged = self._serialize_rule_base(row)
        merged.update(payload)
        fields = self._normalize_rule_payload(merged, source=merged.get("source") or "api")
        updated = self.repo.update_rule(rule_id, fields)
        if updated is None:
            raise AlertNotFoundError(f"Alert rule not found: {rule_id}")
        return self._serialize_rule(updated)

    def delete_rule(self, rule_id: int) -> bool:
        return self.repo.delete_rule(rule_id)

    def enable_rule(self, rule_id: int, enabled: bool) -> Dict[str, Any]:
        updated = self.repo.update_rule(rule_id, {"enabled": enabled})
        if updated is None:
            raise AlertNotFoundError(f"Alert rule not found: {rule_id}")
        return self._serialize_rule(updated)

    def list_rules(
        self,
        *,
        enabled: Optional[bool] = None,
        alert_type: Optional[str] = None,
        target_scope: Optional[str] = None,
        target: Optional[str] = None,
        source: Optional[str] = None,
        cs_only: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        rows, total = self.repo.list_rules(
            enabled=enabled,
            alert_type=alert_type,
            target_scope=target_scope,
            target=target,
            source=source,
            cs_only=cs_only or True,
            page=page,
            page_size=page_size,
        )
        return {
            "items": [self._serialize_rule(row) for row in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def test_rule(self, rule_id: int) -> Dict[str, Any]:
        row = self.repo.get_rule(rule_id)
        if row is None:
            raise AlertNotFoundError(f"Alert rule not found: {rule_id}")

        payloads = self.build_runtime_payloads(row)
        try:
            if len(payloads) == 1:
                result = asyncio.run(self._evaluate_rule(payloads[0].rule))
                return self._dry_run_response_for_single(payloads[0], result, target_scope=row.target_scope)
            results = asyncio.run(self._evaluate_runtime_payloads(payloads))
            return aggregate_dry_run_results(rule_id, row.target_scope, results)
        except Exception as exc:
            sanitized_message = self._sanitize_text(str(exc) or "Alert evaluation failed")
            return {
                "rule_id": rule_id,
                "target_scope": row.target_scope,
                "status": "evaluation_error",
                "record_status": "failed",
                "triggered": False,
                "observed_value": None,
                "threshold": None,
                "data_source": None,
                "data_timestamp": None,
                "reason": sanitized_message,
                "message": sanitized_message,
                "evaluated_count": 0,
                "triggered_count": 0,
                "degraded_count": 0,
                "skipped_count": 0,
                "target_results": [],
            }

    async def _evaluate_rule(self, rule) -> Dict[str, Any]:
        if isinstance(rule, CSHoldingsAlert):
            return await asyncio.to_thread(evaluate_cs_holdings_alert, rule)
        if isinstance(rule, StaticAlertEvaluation):
            return evaluate_static_alert(rule)
        return self._evaluation_error(rule, f"unsupported runtime alert type: {getattr(rule, 'alert_type', rule)}")

    async def _evaluate_runtime_payloads(self, payloads: List[RuntimeAlertPayload]) -> List[Dict[str, Any]]:
        semaphore = asyncio.Semaphore(8)

        async def _evaluate_one(payload: RuntimeAlertPayload) -> Dict[str, Any]:
            async with semaphore:
                try:
                    result = await asyncio.wait_for(
                        self._evaluate_rule(payload.rule),
                        timeout=DRY_RUN_TARGET_TIMEOUT_SECONDS,
                    )
                except asyncio.TimeoutError:
                    result = {
                        "rule_id": self._runtime_rule_id(payload.rule),
                        "status": "not_triggered",
                        "record_status": "skipped",
                        "triggered": False,
                        "observed_value": None,
                        "threshold": self._threshold_for_rule(payload.rule),
                        "data_source": self._data_source_for_rule(payload.rule),
                        "data_timestamp": None,
                        "reason": "dry-run evaluation timed out",
                        "message": "dry-run evaluation timed out",
                    }
                except Exception as exc:
                    sanitized_message = self._sanitize_text(str(exc) or "Alert evaluation failed")
                    result = {
                        "rule_id": self._runtime_rule_id(payload.rule),
                        "status": "evaluation_error",
                        "record_status": "failed",
                        "triggered": False,
                        "observed_value": None,
                        "threshold": self._threshold_for_rule(payload.rule),
                        "data_source": self._data_source_for_rule(payload.rule),
                        "data_timestamp": None,
                        "reason": sanitized_message,
                        "message": sanitized_message,
                    }
                return result_to_target_result(payload, result)

        tasks = [asyncio.create_task(_evaluate_one(payload)) for payload in payloads]
        done, pending = await asyncio.wait(tasks, timeout=DRY_RUN_TOTAL_TIMEOUT_SECONDS)
        for task in pending:
            task.cancel()
        output: List[Dict[str, Any]] = []
        for task in done:
            output.append(task.result())
        for task, payload in zip(tasks, payloads):
            if task in pending:
                output.append({
                    "target": payload.effective_target,
                    "display_target": payload.display_target,
                    "status": "not_triggered",
                    "record_status": "skipped",
                    "triggered": False,
                    "observed_value": None,
                    "threshold": None,
                    "message": "dry-run evaluation timed out",
                })
        return output

    @staticmethod
    def _dry_run_response_for_single(payload: RuntimeAlertPayload, result: Dict[str, Any], *, target_scope: str) -> Dict[str, Any]:
        target_result = result_to_target_result(payload, result)
        return {
            "rule_id": result.get("rule_id") or 0,
            "target_scope": target_scope,
            "status": result.get("status") or "evaluation_error",
            "triggered": bool(result.get("triggered")),
            "observed_value": result.get("observed_value"),
            "message": result.get("message") or result.get("reason") or "",
            "evaluated_count": 1,
            "triggered_count": 1 if result.get("triggered") else 0,
            "degraded_count": 1 if result.get("record_status") == "degraded" else 0,
            "skipped_count": 1 if result.get("record_status") == "skipped" else 0,
            "target_results": [target_result],
        }

    def _triggered(self, rule, observed_value: Any, message: str, **kwargs) -> Dict[str, Any]:
        sanitized_message = self._sanitize_text(message)
        return {
            "rule_id": self._runtime_rule_id(rule),
            "status": "triggered",
            "record_status": "triggered",
            "triggered": True,
            "observed_value": observed_value,
            "threshold": kwargs.get("threshold"),
            "data_source": kwargs.get("data_source"),
            "data_timestamp": kwargs.get("data_timestamp"),
            "reason": sanitized_message,
            "message": sanitized_message,
        }

    def _not_triggered(self, rule, observed_value: Any, message: str, **kwargs) -> Dict[str, Any]:
        sanitized_message = self._sanitize_text(message)
        return {
            "rule_id": self._runtime_rule_id(rule),
            "status": "not_triggered",
            "record_status": kwargs.get("record_status"),
            "triggered": False,
            "observed_value": observed_value,
            "threshold": kwargs.get("threshold"),
            "data_source": kwargs.get("data_source"),
            "data_timestamp": kwargs.get("data_timestamp"),
            "reason": sanitized_message,
            "message": sanitized_message,
        }

    def _evaluation_error(self, rule, exc: Any, **kwargs) -> Dict[str, Any]:
        sanitized_message = self._sanitize_text(str(exc) or "Alert evaluation failed")
        return {
            "rule_id": self._runtime_rule_id(rule),
            "status": "evaluation_error",
            "record_status": "failed",
            "triggered": False,
            "observed_value": None,
            "threshold": kwargs.get("threshold", self._threshold_for_rule(rule)),
            "data_source": kwargs.get("data_source", self._data_source_for_rule(rule)),
            "data_timestamp": kwargs.get("data_timestamp"),
            "reason": sanitized_message,
            "message": sanitized_message,
        }

    @staticmethod
    def _runtime_rule_id(rule) -> int:
        metadata = getattr(rule, "metadata", None) or {}
        return int(metadata.get("persisted_rule_id", 0) or 0)

    @staticmethod
    def _threshold_for_rule(rule) -> Optional[float]:
        if isinstance(rule, CSHoldingsAlert):
            if rule.alert_type == "cs_price_cross":
                return float(rule.parameters.get("price") or 0)
            if rule.alert_type == "cs_pnl_threshold":
                return float(rule.parameters.get("threshold_pct") or 0)
        return None

    @staticmethod
    def _data_source_for_rule(rule) -> Optional[str]:
        if isinstance(rule, CSHoldingsAlert):
            if rule.alert_type == "cs_price_cross":
                return "csqaq"
            if rule.alert_type in {"cs_concentration", "cs_stop_loss", "cs_price_stale"}:
                return "cs_holdings_risk"
            return "cs_holdings_snapshot"
        return None

    def list_triggers(
        self,
        *,
        rule_id: Optional[int] = None,
        target: Optional[str] = None,
        status: Optional[str] = None,
        cs_only: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        rows, total = self.repo.list_triggers(
            rule_id=rule_id,
            target=target,
            status=status,
            cs_only=cs_only or True,
            page=page,
            page_size=page_size,
        )
        return {
            "items": [self._serialize_trigger(row) for row in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def list_notifications(
        self,
        *,
        trigger_id: Optional[int] = None,
        channel: Optional[str] = None,
        success: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        rows, total = self.repo.list_notifications(
            trigger_id=trigger_id,
            channel=channel,
            success=success,
            page=page,
            page_size=page_size,
        )
        return {
            "items": [self._serialize_notification(row) for row in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def _normalize_rule_payload(self, payload: Dict[str, Any], *, source: str = "api") -> Dict[str, Any]:
        target_scope = str(payload.get("target_scope") or "cs_holdings").strip()
        if target_scope not in SUPPORTED_TARGET_SCOPES:
            raise AlertServiceError(f"unsupported target_scope: {target_scope}")

        target = str(payload.get("target") or "").strip()
        if not target:
            raise AlertServiceError("target is required")

        alert_type = str(payload.get("alert_type") or "").strip().lower()
        if alert_type not in SUPPORTED_ALERT_TYPES:
            raise UnsupportedAlertTypeError(f"unsupported alert_type for Alert API: {alert_type or '<empty>'}")
        self._validate_scope_alert_type(target_scope, alert_type)

        severity = str(payload.get("severity") or "warning").strip().lower()
        if severity not in SUPPORTED_SEVERITIES:
            raise AlertServiceError(f"unsupported severity: {severity}")

        parameters = self._normalize_parameters(alert_type, payload.get("parameters") or {})
        target = self._normalize_target(target_scope, target)

        name = str(payload.get("name") or "").strip()
        if not name:
            name = self._default_rule_name(target=target, alert_type=alert_type, parameters=parameters)

        return {
            "name": name[:64],
            "target_scope": target_scope,
            "target": target,
            "alert_type": alert_type,
            "parameters": self._dump_json(parameters),
            "severity": severity,
            "enabled": bool(payload.get("enabled", True)),
            "source": str(source or "api")[:16],
            "cooldown_policy": self._dump_json_or_none(payload.get("cooldown_policy")),
            "notification_policy": self._dump_json_or_none(payload.get("notification_policy")),
        }

    def _validate_rule_update_payload(self, payload: Dict[str, Any]) -> None:
        for field_name, value in payload.items():
            if value is None and field_name not in NULLABLE_RULE_UPDATE_FIELDS:
                raise AlertServiceError(f"{field_name} must not be null")

    @staticmethod
    def _validate_scope_alert_type(target_scope: str, alert_type: str) -> None:
        if target_scope in CS_HOLDINGS_TARGET_SCOPES:
            if alert_type not in CS_HOLDINGS_ALERT_TYPES:
                raise AlertServiceError(f"{target_scope} only supports CS holdings alert types")
            if target_scope == "cs_item" and alert_type != "cs_price_cross":
                raise AlertServiceError("cs_item only supports cs_price_cross")
            return
        raise AlertServiceError("only CS holdings alert scopes are supported")

    def _normalize_target(self, target_scope: str, target: str) -> str:
        try:
            return normalize_cs_target(target_scope, target)
        except ValueError as exc:
            raise AlertServiceError(str(exc)) from exc

    def _normalize_parameters(self, alert_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(parameters, dict):
            raise AlertServiceError("parameters must be an object")
        try:
            return normalize_cs_alert_parameters(alert_type, parameters)
        except ValueError as exc:
            raise AlertServiceError(str(exc)) from exc

    def build_runtime_payloads(
        self,
        row: AlertRuleRecord,
        *,
        config: Optional[Any] = None,
        include_overflow_payload: bool = True,
    ) -> List[RuntimeAlertPayload]:
        data = self._serialize_rule_base(row)
        parent_key = self._semantic_key(
            data["target_scope"],
            data["target"],
            data["alert_type"],
            data["parameters"],
        )

        if data["alert_type"] == "cs_price_cross" and data["target_scope"] == "cs_holdings":
            return self._build_cs_price_cross_payloads(parent_key=parent_key, data=data)
        return [make_cs_holdings_payload(parent_key=parent_key, data=data)]

    def _build_cs_price_cross_payloads(self, *, parent_key: str, data: Dict[str, Any]) -> List[RuntimeAlertPayload]:
        try:
            targets, overflow_count = expand_cs_item_targets(
                target_scope=data["target_scope"],
                target=data["target"],
            )
        except Exception as exc:
            return [
                make_static_payload(
                    parent_key=parent_key,
                    rule_id=int(data["id"] or 0),
                    alert_type=data["alert_type"],
                    effective_target=f"{data['target_scope']}:{data['target']}",
                    display_target="CS 持仓展开失败",
                    message=self._sanitize_text(str(exc) or "target expansion failed"),
                    record_status="failed",
                )
            ]

        payloads: List[RuntimeAlertPayload] = []
        for target in targets:
            child_data = dict(data)
            child_data["target_scope"] = "cs_item"
            child_data["target"] = str(target["good_id"])
            rule = CSHoldingsAlert(
                target_scope="cs_item",
                target=str(target["good_id"]),
                alert_type=child_data["alert_type"],
                parameters=dict(child_data.get("parameters") or {}),
                metadata={
                    "persisted_rule_id": child_data["id"],
                    "effective_target": cs_effective_target("cs_item", str(target["good_id"])),
                    "display_target": str(target.get("item_name") or target["good_id"]),
                },
                description=child_data.get("name") or child_data["alert_type"],
            )
            effective_target = cs_effective_target("cs_item", str(target["good_id"]))
            payloads.append(
                RuntimeAlertPayload(
                    key=f"{parent_key}|{effective_target}",
                    rule=rule,
                    effective_target=effective_target,
                    display_target=str(target.get("item_name") or target["good_id"]),
                )
            )
        if overflow_count:
            payloads.append(
                make_static_payload(
                    parent_key=parent_key,
                    rule_id=int(data["id"] or 0),
                    alert_type=data["alert_type"],
                    effective_target=f"{data['target_scope']}:{data['target']}:overflow",
                    display_target="展开目标超限",
                    message=f"Skipped {overflow_count} CS items over soft cap",
                    record_status="degraded",
                )
            )
        if not payloads:
            payloads.append(
                make_static_payload(
                    parent_key=parent_key,
                    rule_id=int(data["id"] or 0),
                    alert_type=data["alert_type"],
                    effective_target=f"{data['target_scope']}:{data['target']}",
                    display_target="CS 持仓",
                    message="No CS holdings with good_id to evaluate",
                    record_status="skipped",
                )
            )
        return payloads

    @staticmethod
    def _semantic_key(target_scope: str, target: str, alert_type: str, parameters: Dict[str, Any]) -> str:
        canonical_params = json.dumps(parameters or {}, ensure_ascii=False, sort_keys=True)
        return f"{target_scope}:{target}:{alert_type}:{canonical_params}"

    def _serialize_rule(self, row: AlertRuleRecord) -> Dict[str, Any]:
        data = self._serialize_rule_base(row)
        cooldown_summary = self._cooldown_summary_for_rule(row)
        data.update({
            "last_triggered_at": cooldown_summary.get("last_triggered_at"),
            "cooldown_until": cooldown_summary.get("cooldown_until"),
            "cooldown_active": cooldown_summary.get("cooldown_active"),
        })
        return data

    def _serialize_rule_base(self, row: AlertRuleRecord) -> Dict[str, Any]:
        return {
            "id": row.id,
            "name": row.name,
            "target_scope": row.target_scope,
            "target": row.target,
            "alert_type": row.alert_type,
            "parameters": self._load_json(row.parameters, default={}),
            "severity": row.severity,
            "enabled": bool(row.enabled),
            "source": row.source,
            "cooldown_policy": self._load_json(row.cooldown_policy, default=None),
            "notification_policy": self._load_json(row.notification_policy, default=None),
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        }

    def _cooldown_summary_for_rule(self, row: AlertRuleRecord) -> Dict[str, Any]:
        try:
            cooldown_target = cs_effective_target(str(row.target_scope), str(row.target))
            cooldown = self.repo.get_rule_cooldown_summary(
                rule_id=int(row.id),
                target=cooldown_target,
                severity=str(row.severity) if row.severity else None,
            )
        except Exception as exc:
            logger.warning(
                "[AlertService] Failed to load alert cooldown summary for rule %s: %s",
                getattr(row, "id", "?"),
                self._sanitize_text(str(exc) or "cooldown summary read failed"),
            )
            return {"last_triggered_at": None, "cooldown_until": None, "cooldown_active": False}
        return self._serialize_cooldown_summary(cooldown)

    @staticmethod
    def _serialize_cooldown_summary(row: Optional[AlertCooldownRecord]) -> Dict[str, Any]:
        if row is None:
            return {"last_triggered_at": None, "cooldown_until": None, "cooldown_active": False}
        cooldown_active = bool(
            row.state == "active"
            and row.cooldown_until is not None
            and row.cooldown_until > datetime.now()
        )
        return {
            "last_triggered_at": row.last_triggered_at.isoformat() if row.last_triggered_at else None,
            "cooldown_until": row.cooldown_until.isoformat() if row.cooldown_until else None,
            "cooldown_active": cooldown_active,
        }

    def _serialize_trigger(self, row: AlertTriggerRecord) -> Dict[str, Any]:
        return {
            "id": row.id,
            "rule_id": row.rule_id,
            "target": row.target,
            "observed_value": row.observed_value,
            "threshold": row.threshold,
            "reason": row.reason,
            "data_source": row.data_source,
            "data_timestamp": row.data_timestamp.isoformat() if row.data_timestamp else None,
            "triggered_at": row.triggered_at.isoformat() if row.triggered_at else None,
            "status": row.status,
            "diagnostics": self._sanitize_text(row.diagnostics) if row.diagnostics else None,
        }

    def _serialize_notification(self, row: AlertNotificationRecord) -> Dict[str, Any]:
        return {
            "id": row.id,
            "trigger_id": row.trigger_id,
            "channel": row.channel,
            "attempt": row.attempt,
            "success": bool(row.success),
            "error_code": row.error_code,
            "retryable": bool(row.retryable),
            "latency_ms": row.latency_ms,
            "diagnostics": self._sanitize_text(row.diagnostics) if row.diagnostics else None,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }

    @staticmethod
    def _default_rule_name(*, target: str, alert_type: str, parameters: Dict[str, Any]) -> str:
        if alert_type == "cs_price_cross":
            return f"{target} CS price {parameters['direction']} {parameters['price']}"
        if alert_type == "cs_pnl_threshold":
            return f"{target} CS pnl {parameters['direction']} {parameters['threshold_pct']}%"
        if alert_type == "cs_price_stale":
            return f"{target} CS stale price"
        if alert_type == "cs_concentration":
            return f"{target} CS concentration"
        if alert_type == "cs_stop_loss":
            return f"{target} CS stop loss {parameters.get('mode', 'near')}"
        return f"{target} {alert_type}"

    @staticmethod
    def _dump_json(value: Dict[str, Any]) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)

    def _dump_json_or_none(self, value: Optional[Dict[str, Any]]) -> Optional[str]:
        if value is None:
            return None
        if not isinstance(value, dict):
            raise AlertServiceError("policy fields must be objects")
        return self._dump_json(value)

    @staticmethod
    def _load_json(raw: Optional[str], *, default: Any) -> Any:
        if raw is None or raw == "":
            return default
        try:
            return json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            return default

    @staticmethod
    def _sanitize_text(text: Any) -> str:
        return sanitize_diagnostic_text(text)
