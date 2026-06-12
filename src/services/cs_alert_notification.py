# -*- coding: utf-8 -*-
"""CS alert notification: batched email with structured facts and optional AI summary."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, TYPE_CHECKING

if TYPE_CHECKING:
    from src.config import Config
    from src.notification import NotificationDispatchResult
    from src.services.alert_worker import RuntimeAlertRule

from src.services.cs_alerts import dedupe_cs_holding_top_items

logger = logging.getLogger(__name__)

CS_ALERT_TYPES = frozenset({
    "cs_price_cross",
    "cs_pnl_threshold",
    "cs_price_stale",
    "cs_concentration",
    "cs_stop_loss",
})


@dataclass
class AlertNotificationItem:
    display_target: str
    effective_target: str
    rule_name: str
    alert_type: str
    target_scope: str
    reason: str
    observed_value: Optional[float] = None
    threshold: Optional[float] = None
    data_source: Optional[str] = None
    data_timestamp: Optional[str] = None
    item_name: Optional[str] = None
    platform: Optional[str] = None
    action_label: Optional[str] = None
    pnl_pct: Optional[float] = None
    cost_price: Optional[float] = None
    diagnostics: Dict[str, Any] = field(default_factory=dict)
    is_cs: bool = False


def _safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_diagnostics(raw: Any) -> Dict[str, Any]:
    if isinstance(raw, dict):
        return dict(raw)
    if isinstance(raw, str) and raw.strip():
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
    return {}


def _resolve_action_label(rule_name: str, alert_type: str, parameters: Dict[str, Any]) -> Optional[str]:
    name = (rule_name or "").lower()
    if "止盈" in rule_name or "take_profit" in name:
        return "止盈"
    if "止损" in rule_name or "stop_loss" in name:
        return "止损"
    if alert_type == "cs_price_cross":
        direction = str(parameters.get("direction") or "").lower()
        return "止盈" if direction == "above" else "止损"
    if alert_type == "cs_stop_loss":
        return "止损监控"
    if alert_type == "cs_concentration":
        return "集中度"
    if alert_type == "cs_price_stale":
        return "价格过期"
    if alert_type == "cs_pnl_threshold":
        direction = str(parameters.get("direction") or "").lower()
        return "盈利阈值" if direction == "gain" else "亏损阈值"
    return None


def _lookup_holding_by_good_id(good_id: int, platform: Optional[str]) -> Optional[Dict[str, Any]]:
    try:
        from src.services.cs_holdings_service import CSHoldingsService

        snapshot = CSHoldingsService().get_snapshot(refresh_prices=False)
        plat = (platform or "").strip().lower()
        matched: List[Dict[str, Any]] = []
        for row in snapshot.get("items") or []:
            if int(row.get("good_id") or 0) != good_id:
                continue
            row_plat = str(row.get("platform") or "yyyp").lower()
            if plat and plat not in {"all", row_plat}:
                continue
            matched.append(row)
        if not matched:
            return None
        if len(matched) == 1:
            return matched[0]

        total_qty = 0
        cost_sum = 0.0
        market_price: Optional[float] = None
        item_name = str(matched[0].get("item_name") or good_id)
        for row in matched:
            qty = max(1, int(row.get("quantity") or 1))
            purchase = _safe_float(row.get("purchase_price"))
            if purchase is not None and purchase > 0:
                cost_sum += purchase * qty
                total_qty += qty
            mp = _safe_float(row.get("market_price"))
            if mp is not None:
                market_price = mp
            name = str(row.get("item_name") or "")
            if len(name) > len(item_name):
                item_name = name

        avg_cost = (cost_sum / total_qty) if total_qty > 0 else None
        pnl_pct: Optional[float] = None
        if avg_cost and avg_cost > 0 and market_price is not None:
            pnl_pct = (market_price - avg_cost) / avg_cost * 100.0
        return {
            "item_name": item_name,
            "purchase_price": avg_cost,
            "pnl_pct": pnl_pct,
            "market_price": market_price,
            "lot_count": len(matched),
        }
    except Exception as exc:
        logger.debug("CS alert holding lookup failed good_id=%s: %s", good_id, exc)
    return None


def normalize_alert_item(
    runtime_rule: "RuntimeAlertRule",
    result: Dict[str, Any],
) -> AlertNotificationItem:
    rule = runtime_rule.rule
    alert_type = str(getattr(rule, "alert_type", "") or "").strip().lower()
    target_scope = str(getattr(rule, "target_scope", "") or "single_symbol").strip().lower()
    parameters = dict(getattr(rule, "parameters", None) or {})
    rule_name = str(getattr(rule, "description", "") or runtime_rule.display_target or alert_type)
    diagnostics = _parse_diagnostics(result.get("diagnostics"))
    is_cs = alert_type in CS_ALERT_TYPES or target_scope in {"cs_item", "cs_holdings"}

    item = AlertNotificationItem(
        display_target=str(runtime_rule.display_target or runtime_rule.effective_target or "?"),
        effective_target=str(runtime_rule.effective_target or "?"),
        rule_name=rule_name,
        alert_type=alert_type or "unknown",
        target_scope=target_scope,
        reason=str(result.get("reason") or result.get("message") or rule_name),
        observed_value=_safe_float(result.get("observed_value")),
        threshold=_safe_float(result.get("threshold")),
        data_source=result.get("data_source"),
        data_timestamp=result.get("data_timestamp"),
        diagnostics=diagnostics,
        is_cs=is_cs,
        platform=str(parameters.get("platform") or diagnostics.get("platform") or "") or None,
        action_label=_resolve_action_label(rule_name, alert_type, parameters),
    )

    if target_scope == "cs_item":
        good_id_raw = getattr(rule, "target", None) or diagnostics.get("good_id")
        try:
            good_id = int(good_id_raw)
        except (TypeError, ValueError):
            good_id = None
        if good_id is not None:
            holding = _lookup_holding_by_good_id(good_id, item.platform)
            if holding:
                item.item_name = str(holding.get("item_name") or item.display_target)
                item.pnl_pct = _safe_float(holding.get("pnl_pct"))
                item.cost_price = _safe_float(holding.get("purchase_price"))
            elif not item.item_name:
                item.item_name = item.display_target.replace("饰品 ", "", 1)

    return item


def build_alert_subject(items: Sequence[AlertNotificationItem], config: "Config") -> str:
    prefix = str(getattr(config, "cs_alert_email_subject_prefix", None) or "【CS价格预警】").strip()
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    if len(items) == 1:
        item = items[0]
        label = item.item_name or item.display_target
        action = f" · {item.action_label}" if item.action_label else ""
        return f"{prefix}{label}{action} · {stamp}"
    return f"{prefix}{len(items)} 条触发 · {stamp}"


def _format_money(value: Optional[float]) -> str:
    if value is None:
        return "—"
    return f"¥{value:,.2f}"


def _format_pct(value: Optional[float]) -> str:
    if value is None:
        return "—"
    return f"{value:+.2f}%"


def _escape_md_cell(value: Any) -> str:
    text = str(value if value not in (None, "") else "—")
    return text.replace("|", "\\|").replace("\n", " ").strip()


def _display_item_label(item: AlertNotificationItem) -> str:
    return item.item_name or item.display_target.replace("饰品 ", "", 1)


def _collect_related_holdings(item: AlertNotificationItem) -> List[Dict[str, Any]]:
    if item.target_scope == "cs_item":
        return []
    raw = item.diagnostics.get("top_items") or item.diagnostics.get("top_positions") or []
    if not isinstance(raw, list):
        return []
    return dedupe_cs_holding_top_items(raw, limit=8)


def _render_overview_table(items: Sequence[AlertNotificationItem]) -> List[str]:
    if not items:
        return []
    lines = [
        "## 预警概览",
        "",
        "| # | 饰品 | 类型 | 现价 | 阈值 | 盈亏 |",
        "| ---: | --- | --- | ---: | ---: | ---: |",
    ]
    for index, item in enumerate(items, start=1):
        if not item.is_cs:
            continue
        lines.append(
            "| {idx} | {name} | {action} | {price} | {threshold} | {pnl} |".format(
                idx=index,
                name=_escape_md_cell(_display_item_label(item)),
                action=_escape_md_cell(item.action_label or "—"),
                price=_escape_md_cell(_format_money(item.observed_value)),
                threshold=_escape_md_cell(_format_money(item.threshold)),
                pnl=_escape_md_cell(_format_pct(item.pnl_pct)),
            )
        )
    lines.append("")
    return lines


def _render_detail_table(rows: List[tuple[str, str]]) -> List[str]:
    if not rows:
        return []
    lines = [
        "| 项目 | 内容 |",
        "| --- | --- |",
    ]
    for label, value in rows:
        lines.append(f"| {_escape_md_cell(label)} | {_escape_md_cell(value)} |")
    lines.append("")
    return lines


def _render_related_holdings_table(rows: List[Dict[str, Any]]) -> List[str]:
    if not rows:
        return []
    lines = [
        "**相关持仓**",
        "",
        "| 饰品 | 盈亏 |",
        "| --- | ---: |",
    ]
    for row in rows:
        name = row.get("item_name") or row.get("good_id") or "?"
        pnl = row.get("pnl_pct")
        if pnl is None:
            loss = _safe_float(row.get("loss_pct"))
            pnl_text = f"-{loss:.2f}%" if loss is not None else "—"
        else:
            pnl_text = _format_pct(float(pnl))
        lines.append(f"| {_escape_md_cell(name)} | {_escape_md_cell(pnl_text)} |")
    lines.append("")
    return lines


def _render_cs_item_section(item: AlertNotificationItem, index: int) -> List[str]:
    scope_label = "单品" if item.target_scope == "cs_item" else "全仓"
    title = _display_item_label(item)
    action = item.action_label or "预警"
    lines = [
        f"### {index}. {title} · {action}",
        "",
    ]

    detail_rows: List[tuple[str, str]] = [("范围", scope_label)]
    if item.action_label:
        detail_rows.append(("类型", item.action_label))
    if item.rule_name:
        detail_rows.append(("规则", item.rule_name))
    if item.platform:
        detail_rows.append(("平台", item.platform))
    if item.observed_value is not None:
        detail_rows.append(("现价", _format_money(item.observed_value)))
    if item.threshold is not None:
        detail_rows.append(("阈值", _format_money(item.threshold)))
    if item.cost_price is not None:
        detail_rows.append(("成本价", _format_money(item.cost_price)))
    if item.pnl_pct is not None:
        detail_rows.append(("持仓盈亏", _format_pct(item.pnl_pct)))
    if item.data_source:
        detail_rows.append(("数据来源", str(item.data_source)))
    detail_rows.append(("说明", item.reason))
    lines.extend(_render_detail_table(detail_rows))

    related = _collect_related_holdings(item)
    if related:
        lines.extend(_render_related_holdings_table(related))
    return lines


def _render_generic_section(item: AlertNotificationItem, index: int) -> List[str]:
    lines = [
        f"### {index}. {item.display_target}",
        "",
        f"- **规则**：{item.rule_name}",
    ]
    if item.observed_value is not None:
        lines.append(f"- **观测值**：{item.observed_value}")
    if item.threshold is not None:
        lines.append(f"- **阈值**：{item.threshold}")
    lines.append(f"- **说明**：{item.reason}")
    lines.append("")
    return lines


def build_alert_markdown(
    items: Sequence[AlertNotificationItem],
    *,
    ai_summary: Optional[str] = None,
) -> str:
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cs_count = sum(1 for item in items if item.is_cs)
    lines = [
        f"# ⚠️ CS 饰品价格预警 · {len(items)} 条触发",
        "",
        f"> 触发时间：{stamp} | CS 规则 {cs_count} 条 | 其他 {len(items) - cs_count} 条",
        "",
    ]
    if ai_summary:
        lines.extend(["## AI 解读", "", ai_summary.strip(), ""])

    cs_items = [item for item in items if item.is_cs]
    if len(cs_items) > 1:
        lines.extend(_render_overview_table(cs_items))

    lines.extend(["## 触发明细", ""])
    for index, item in enumerate(items, start=1):
        if item.is_cs:
            lines.extend(_render_cs_item_section(item, index))
        else:
            lines.extend(_render_generic_section(item, index))

    lines.extend([
        "---",
        "",
        "*24 小时内同规则不重复通知；以上为系统自动监控结果，非投资建议。*",
    ])
    return "\n".join(lines)


def _build_alert_ai_prompt(items: Sequence[AlertNotificationItem]) -> str:
    payload = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        label = _display_item_label(item)
        action = item.action_label or ""
        key = (label, action)
        if key in seen:
            continue
        seen.add(key)
        payload.append({
            "display_target": item.display_target,
            "item_name": label,
            "alert_type": item.alert_type,
            "action_label": item.action_label,
            "observed_value": item.observed_value,
            "threshold": item.threshold,
            "pnl_pct": item.pnl_pct,
            "reason": item.reason,
            "target_scope": item.target_scope,
        })
    facts = json.dumps(payload, ensure_ascii=False, indent=2)
    return (
        "你是 CS2 饰品交易助手。以下告警已由系统判定触发，请基于给定事实写中文总结。\n"
        "要求：\n"
        "1. 先写 2-3 句总览（整体风险与优先关注项）\n"
        "2. 再逐条写一行建议（持有/减仓/观望/复核数据），不要编造未提供的价格\n"
        "3. 总字数 150-350 字，不要使用 Markdown 标题\n"
        f"\n告警事实 JSON：\n{facts}\n"
    )


def generate_alert_ai_summary(
    items: Sequence[AlertNotificationItem],
    config: "Config",
) -> Optional[str]:
    if not getattr(config, "cs_alert_ai_summary_enabled", True):
        return None
    try:
        from src.analyzer import GeminiAnalyzer

        analyzer = GeminiAnalyzer()
        if not analyzer.is_available():
            return None
        text = analyzer.generate_text(
            _build_alert_ai_prompt(items),
            max_tokens=512,
            temperature=0.4,
        )
        return (text or "").strip() or None
    except Exception as exc:
        logger.warning("CS alert AI summary failed: %s", exc)
        return None


def send_batched_alert_notification(
    entries: Sequence[Any],
    *,
    notifier: Any,
    config: "Config",
) -> "NotificationDispatchResult":
    """Build and send one batched alert notification for multiple triggered rules."""
    from src.notification import NotificationService

    notification_service = notifier or NotificationService()
    items = [
        normalize_alert_item(entry.runtime_rule, entry.result)
        for entry in entries
    ]
    ai_summary = generate_alert_ai_summary(items, config)
    body = build_alert_markdown(items, ai_summary=ai_summary)
    subject = build_alert_subject(items, config)
    return notification_service.send_with_results(
        body,
        route_type="alert",
        email_send_to_all=True,
        email_subject=subject,
        severity="warning",
    )
