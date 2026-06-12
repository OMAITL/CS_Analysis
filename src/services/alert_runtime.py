# -*- coding: utf-8 -*-
"""Shared runtime types for CS alert evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

TARGET_RESULTS_LIMIT = 20
DRY_RUN_TARGET_TIMEOUT_SECONDS = 10
DRY_RUN_TOTAL_TIMEOUT_SECONDS = 30


@dataclass(frozen=True)
class RuntimeAlertPayload:
    """Runtime rule plus the identity used for cooldown/history."""

    key: str
    rule: Any
    effective_target: str
    display_target: str


@dataclass
class StaticAlertEvaluation:
    """Runtime placeholder for skipped/degraded expansion results."""

    stock_code: str
    alert_type: str
    message: str
    record_status: str = "skipped"
    metadata: Dict[str, Any] = field(default_factory=dict)
    description: str = ""


def make_static_payload(
    *,
    parent_key: str,
    rule_id: int,
    alert_type: str,
    effective_target: str,
    display_target: str,
    message: str,
    record_status: str = "skipped",
) -> RuntimeAlertPayload:
    rule = StaticAlertEvaluation(
        stock_code=effective_target,
        alert_type=alert_type,
        message=message,
        record_status=record_status,
        metadata={
            "persisted_rule_id": rule_id,
            "effective_target": effective_target,
            "display_target": display_target,
        },
        description=message,
    )
    return RuntimeAlertPayload(
        key=f"{parent_key}|{effective_target}",
        rule=rule,
        effective_target=effective_target,
        display_target=display_target,
    )


def evaluate_static_alert(rule: StaticAlertEvaluation) -> Dict[str, Any]:
    return {
        "rule_id": int(rule.metadata.get("persisted_rule_id", 0) or 0),
        "status": "not_triggered",
        "record_status": rule.record_status,
        "triggered": False,
        "observed_value": None,
        "threshold": None,
        "data_source": None,
        "data_timestamp": None,
        "reason": rule.message,
        "message": rule.message,
    }


def result_to_target_result(payload: RuntimeAlertPayload, result: Dict[str, Any]) -> Dict[str, Any]:
    record_status = result.get("record_status")
    return {
        "target": payload.effective_target,
        "display_target": payload.display_target,
        "status": result.get("status") or "evaluation_error",
        "record_status": record_status,
        "triggered": bool(result.get("triggered")),
        "observed_value": result.get("observed_value"),
        "threshold": result.get("threshold"),
        "message": result.get("message") or result.get("reason") or "",
    }


def aggregate_dry_run_results(rule_id: int, target_scope: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
    target_results = sorted(
        results,
        key=lambda item: (
            0 if item.get("triggered") else 1,
            0 if item.get("record_status") in {"degraded", "failed"} else 1,
            str(item.get("target") or ""),
        ),
    )
    visible_results = target_results[:TARGET_RESULTS_LIMIT]
    triggered_count = sum(1 for item in target_results if item.get("triggered"))
    degraded_count = sum(1 for item in target_results if item.get("record_status") == "degraded")
    skipped_count = sum(1 for item in target_results if item.get("record_status") == "skipped")
    failed_count = sum(1 for item in target_results if item.get("record_status") == "failed")
    successful_count = sum(
        1
        for item in target_results
        if item.get("record_status") not in {"failed"} and item.get("status") != "evaluation_error"
    )

    if triggered_count:
        status = "triggered"
        triggered = True
    elif successful_count or skipped_count or degraded_count:
        status = "not_triggered"
        triggered = False
    else:
        status = "evaluation_error"
        triggered = False

    if not target_results:
        status = "evaluation_error"
        triggered = False
        message = "No targets were evaluated"
    else:
        message = (
            f"Evaluated {len(target_results)} targets: "
            f"{triggered_count} triggered, {degraded_count} degraded, "
            f"{skipped_count} skipped, {failed_count} failed"
        )

    first_observed = next(
        (item.get("observed_value") for item in target_results if item.get("observed_value") is not None),
        None,
    )
    return {
        "rule_id": rule_id,
        "target_scope": target_scope,
        "status": status,
        "triggered": triggered,
        "observed_value": first_observed,
        "message": message,
        "evaluated_count": len(target_results),
        "triggered_count": triggered_count,
        "degraded_count": degraded_count,
        "skipped_count": skipped_count,
        "target_results": visible_results,
    }
