# -*- coding: utf-8 -*-
"""Daily CS portfolio report: structured data collection + optional AI synthesis + email."""

from __future__ import annotations

import json
import logging
import re
import threading
from datetime import date, datetime, time as dt_time
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from src.config import Config
    from src.notification import NotificationDispatchResult

logger = logging.getLogger(__name__)

_last_sent_lock = threading.Lock()
_last_sent_date: Optional[str] = None

_HOME_SUB_INDEX_NAMES = (
    "饰品指数",
    "租赁指数",
    "百元主战",
    "探员指数",
    "原皮指数",
    "红皮指数",
)


def _parse_hhmm(value: str, default: str = "20:00") -> dt_time:
    candidate = (value or default).strip()
    try:
        hour, minute = candidate.split(":", 1)
        return dt_time(hour=int(hour), minute=int(minute))
    except (TypeError, ValueError):
        return dt_time(hour=20, minute=0)


def _safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _format_money(value: Optional[float]) -> str:
    if value is None:
        return "—"
    return f"¥{value:,.2f}"


def _format_pct(value: Optional[float]) -> str:
    if value is None:
        return "—"
    return f"{value:+.2f}%"


def _escape_md_table_cell(value: Any) -> str:
    text = str(value if value not in (None, "") else "—").replace("|", "\\|")
    return re.sub(r"\s+", " ", text).strip()


def _aggregate_holdings_for_report(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merge duplicate good_id rows (per platform) for ranked top-holdings display."""
    buckets: Dict[Tuple[int, str], Dict[str, Any]] = {}
    passthrough: List[Dict[str, Any]] = []

    for row in items:
        good_id = row.get("good_id")
        if good_id is None:
            passthrough.append(dict(row))
            continue
        try:
            gid = int(good_id)
        except (TypeError, ValueError):
            passthrough.append(dict(row))
            continue
        if gid <= 0:
            passthrough.append(dict(row))
            continue

        platform = str(row.get("platform") or "yyyp").lower()
        qty = max(1, int(row.get("quantity") or 1))
        purchase_price = float(row.get("purchase_price") or 0.0)
        market_price = _safe_float(row.get("market_price"))
        market_total = _safe_float(row.get("market_total"))
        if market_total is None and market_price is not None:
            market_total = market_price * qty

        key = (gid, platform)
        item_name = str(row.get("item_name") or gid).strip() or str(gid)
        bucket = buckets.get(key)
        if bucket is None:
            buckets[key] = {
                "good_id": gid,
                "platform": platform,
                "item_name": item_name,
                "quantity": qty,
                "cost_sum": purchase_price * qty if purchase_price > 0 else 0.0,
                "cost_qty": qty if purchase_price > 0 else 0,
                "market_total": market_total or 0.0,
                "market_price": market_price,
                "lot_count": 1,
            }
            continue

        bucket["quantity"] += qty
        bucket["market_total"] = float(bucket["market_total"]) + float(market_total or 0.0)
        if purchase_price > 0:
            bucket["cost_sum"] = float(bucket["cost_sum"]) + purchase_price * qty
            bucket["cost_qty"] = int(bucket["cost_qty"]) + qty
        bucket["lot_count"] = int(bucket["lot_count"]) + 1
        if len(item_name) > len(str(bucket["item_name"])):
            bucket["item_name"] = item_name
        if market_price is not None:
            bucket["market_price"] = market_price

    aggregated: List[Dict[str, Any]] = []
    for bucket in buckets.values():
        qty = max(1, int(bucket["quantity"]))
        market_total = float(bucket["market_total"])
        market_price = _safe_float(bucket.get("market_price"))
        if market_price is None and qty > 0:
            market_price = market_total / qty if market_total else None

        avg_cost: Optional[float] = None
        cost_qty = int(bucket.get("cost_qty") or 0)
        if cost_qty > 0:
            avg_cost = float(bucket["cost_sum"]) / cost_qty

        pnl_pct: Optional[float] = None
        if avg_cost and avg_cost > 0 and market_price is not None:
            pnl_pct = (market_price - avg_cost) / avg_cost * 100.0

        aggregated.append(
            {
                "good_id": bucket["good_id"],
                "platform": bucket["platform"],
                "item_name": bucket["item_name"],
                "quantity": qty,
                "lot_count": int(bucket["lot_count"]),
                "market_price": market_price,
                "market_total": market_total,
                "purchase_price": round(avg_cost, 4) if avg_cost else None,
                "pnl_pct": round(pnl_pct, 2) if pnl_pct is not None else None,
            }
        )

    aggregated.extend(passthrough)
    return aggregated


def _select_home_sub_indexes(sub_indexes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not sub_indexes:
        return []
    by_name = {
        str(row.get("name") or ""): row
        for row in sub_indexes
        if isinstance(row, dict)
    }
    selected: List[Dict[str, Any]] = []
    seen = set()
    for name in _HOME_SUB_INDEX_NAMES:
        row = by_name.get(name)
        if row is not None:
            selected.append(row)
            seen.add(name)
    for row in sub_indexes:
        name = str(row.get("name") or "")
        if name in seen:
            continue
        selected.append(row)
        if len(selected) >= 6:
            break
    return selected[:6]


def _format_index_line(row: Dict[str, Any], *, bold: bool = False) -> str:
    name = row.get("name") or "指数"
    value = _format_money(_safe_float(row.get("market_index") or row.get("close")))
    chg_num = _safe_float(row.get("chg_num"))
    chg_rate = _safe_float(row.get("chg_rate") if row.get("chg_rate") is not None else row.get("change_pct"))
    chg_parts: List[str] = []
    if chg_num is not None:
        chg_parts.append(_format_money(chg_num))
    if chg_rate is not None:
        chg_parts.append(_format_pct(chg_rate))
    chg_text = " / ".join(chg_parts) if chg_parts else "—"
    line = f"{name}：{value}（{chg_text}）"
    if bold:
        return f"**{line}**"
    return line


def collect_daily_context(config: "Config") -> Dict[str, Any]:
    """Gather structured facts for the daily CS report (no LLM)."""
    today = date.today().isoformat()
    context: Dict[str, Any] = {
        "report_date": today,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "market": {},
        "portfolio": {},
        "risk": {},
        "top_items": [],
    }

    try:
        from src.services.cs_skill_prompt import (
            fetch_cs_home_market,
            fetch_cs_index_summary,
            fetch_cs_rank_leaders,
        )

        home_market = fetch_cs_home_market(sub_index_limit=12)
        if home_market:
            context["market"]["home"] = home_market
            context["market"]["sub_indexes"] = _select_home_sub_indexes(
                list(home_market.get("sub_indexes") or [])
            )
            main_index = home_market.get("main_index") or {}
            if main_index:
                context["market"]["index_summary"] = {
                    "sub_index_id": str(main_index.get("id") or "1"),
                    "latest_close": main_index.get("market_index") or main_index.get("close"),
                    "daily_pct_chg": main_index.get("chg_rate") or main_index.get("change_pct"),
                    "chg_num": main_index.get("chg_num"),
                    "open": main_index.get("open"),
                    "high": main_index.get("high"),
                    "low": main_index.get("low"),
                    "updated_at": main_index.get("updated_at"),
                }
        else:
            index_summary = fetch_cs_index_summary()
            if index_summary:
                context["market"]["index_summary"] = index_summary
    except Exception as exc:
        logger.debug("CS daily report market snapshot failed: %s", exc)

    try:
        from src.services.cs_skill_prompt import fetch_cs_rank_leaders

        rank_limit = max(1, int(getattr(config, "cs_daily_report_rank_items", 5) or 5))
        rank_day = max(1, int(getattr(config, "cs_daily_report_rank_days", 7) or 7))
        rank_leaders = fetch_cs_rank_leaders(day_type=rank_day, limit=rank_limit)
        if rank_leaders:
            context["market"]["rank_leaders"] = rank_leaders
    except Exception as exc:
        logger.debug("CS daily report rank leaders failed: %s", exc)

    try:
        from src.services.cs_holdings_service import CSHoldingsService

        snapshot = CSHoldingsService().get_snapshot(refresh_prices=True)
        context["portfolio"]["summary"] = snapshot.get("summary") or {}
        raw_items = list(snapshot.get("items") or [])
        items = _aggregate_holdings_for_report(raw_items)
        context["portfolio"]["items"] = items
        context["portfolio"]["raw_item_count"] = len(raw_items)
        context["portfolio"]["aggregated_item_count"] = len(items)
    except Exception as exc:
        logger.warning("CS daily report portfolio snapshot failed: %s", exc)
        items = []

    try:
        from src.services.cs_holdings_risk_service import CSHoldingsRiskService

        context["risk"] = CSHoldingsRiskService().get_risk_report(refresh_prices=False)
    except Exception as exc:
        logger.debug("CS daily report risk report failed: %s", exc)

    top_n = max(1, int(getattr(config, "cs_daily_report_top_items", 5) or 5))
    ranked = sorted(
        items,
        key=lambda row: float(row.get("market_total") or 0.0),
        reverse=True,
    )[:top_n]
    context["top_items"] = _collect_top_item_insights(ranked)

    return context


def _collect_top_item_insights(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    insights: List[Dict[str, Any]] = []
    try:
        from src.services.cs_item_data_provider import ItemDataProvider

        provider = ItemDataProvider()
    except Exception:
        provider = None

    for row in items:
        good_id = row.get("good_id")
        entry: Dict[str, Any] = {
            "item_name": row.get("item_name"),
            "good_id": good_id,
            "platform": row.get("platform"),
            "market_price": row.get("market_price"),
            "pnl_pct": row.get("pnl_pct"),
            "market_total": row.get("market_total"),
            "quantity": row.get("quantity"),
            "lot_count": row.get("lot_count"),
        }
        if provider is not None and good_id:
            try:
                bundle = provider.fetch(
                    good_id=int(good_id),
                    platform=row.get("platform"),
                    refresh_today=False,
                    prefer_crawl=True,
                )
                trend = dict(bundle.trend or {})
                entry["trend_status"] = trend.get("trend_status") or trend.get("ma_alignment")
                entry["bias_ma5"] = trend.get("bias_ma5")
                entry["volume_ratio_5d"] = trend.get("volume_ratio_5d")
            except Exception as exc:
                logger.debug("CS daily top item trend failed good_id=%s: %s", good_id, exc)
        insights.append(entry)
    return insights


def build_daily_subject(context: Dict[str, Any], config: "Config") -> str:
    prefix = str(getattr(config, "cs_daily_report_email_subject_prefix", None) or "【CS每日复盘】").strip()
    report_date = context.get("report_date") or date.today().isoformat()
    summary = (context.get("portfolio") or {}).get("summary") or {}
    total_pnl = _safe_float(summary.get("total_pnl"))
    pnl_part = f" · 全仓 {_format_pct(total_pnl)}" if total_pnl is not None else ""
    return f"{prefix}{report_date}{pnl_part}"


def _build_rank_section(rank_leaders: Dict[str, Any]) -> List[str]:
    lines: List[str] = []
    day_type = rank_leaders.get("day_type") or 7
    gainers = list(rank_leaders.get("gainers") or [])
    losers = list(rank_leaders.get("losers") or [])
    error = rank_leaders.get("error")

    lines.extend([f"## 4. 市场涨跌幅榜（近 {day_type} 天）", ""])
    if not gainers and not losers:
        if error:
            lines.append(f"- 榜单数据暂不可用（{error}）")
        else:
            lines.append("- 榜单数据暂不可用")
        lines.append("")
        return lines

    if gainers:
        lines.append("### 涨幅榜 Top 5（百分比）")
        lines.append("")
        lines.append("| 排行 | 饰品 | 在售价 | 涨幅 |")
        lines.append("| --- | --- | --- | --- |")
        for idx, row in enumerate(gainers[:5], start=1):
            lines.append(
                f"| {idx} "
                f"| {_escape_md_table_cell(row.get('name'))} "
                f"| {_format_money(_safe_float(row.get('price')))} "
                f"| {_format_pct(_safe_float(row.get('change_pct')))} |"
            )
        lines.append("")

    if losers:
        lines.append("### 跌幅榜 Top 5（百分比）")
        lines.append("")
        lines.append("| 排行 | 饰品 | 在售价 | 跌幅 |")
        lines.append("| --- | --- | --- | --- |")
        for idx, row in enumerate(losers[:5], start=1):
            lines.append(
                f"| {idx} "
                f"| {_escape_md_table_cell(row.get('name'))} "
                f"| {_format_money(_safe_float(row.get('price')))} "
                f"| {_format_pct(_safe_float(row.get('change_pct')))} |"
            )
        lines.append("")

    return lines


def build_daily_template_markdown(context: Dict[str, Any], *, ai_summary: Optional[str] = None) -> str:
    report_date = context.get("report_date") or date.today().isoformat()
    generated_at = context.get("generated_at") or ""
    summary = (context.get("portfolio") or {}).get("summary") or {}
    market = context.get("market") or {}
    risk = context.get("risk") or {}
    index_summary = market.get("index_summary") or {}
    home_market = market.get("home") or {}
    main_index = home_market.get("main_index") or index_summary

    lines = [
        f"# 📊 CS 饰品每日复盘 · {report_date}",
        "",
        f"> 生成时间 {generated_at} | 持仓 {summary.get('item_count', 0)} 件",
        "",
    ]

    if ai_summary:
        lines.extend(["## AI 总结", "", ai_summary.strip(), ""])

    lines.extend(["## 1. 今日大盘概览", ""])
    if main_index:
        lines.append(f"- {_format_index_line(main_index, bold=True)}")
        open_price = _safe_float(main_index.get("open"))
        high_price = _safe_float(main_index.get("high"))
        low_price = _safe_float(main_index.get("low"))
        if any(value is not None for value in (open_price, high_price, low_price)):
            lines.append(
                "- 今日区间："
                f"开 {_format_money(open_price)} | "
                f"高 {_format_money(high_price)} | "
                f"低 {_format_money(low_price)}"
            )
        updated_at = main_index.get("updated_at")
        if updated_at:
            lines.append(f"- 指数更新时间：{updated_at}")

    sub_indexes = market.get("sub_indexes") or []
    if sub_indexes:
        lines.append("- 子指数：")
        for row in sub_indexes:
            if not isinstance(row, dict):
                continue
            lines.append(f"  - {_format_index_line(row)}")
    if not main_index and not sub_indexes:
        lines.append("- 大盘数据暂不可用")
    lines.append("")

    lines.extend(["## 2. 全仓持仓", ""])
    lines.append(f"- **总市值**：{_format_money(_safe_float(summary.get('total_market_value')))}")
    lines.append(f"- **总成本**：{_format_money(_safe_float(summary.get('total_cost')))}")
    total_pnl = _safe_float(summary.get("total_pnl"))
    total_cost = _safe_float(summary.get("total_cost"))
    pnl_pct = (total_pnl / total_cost * 100.0) if total_pnl is not None and total_cost else None
    lines.append(
        f"- **浮动盈亏**：{_format_money(total_pnl)}（{_format_pct(pnl_pct)}）"
    )
    concentration = risk.get("concentration") or {}
    if concentration:
        lines.append(f"- **最大集中度**：{concentration.get('top_weight_pct', '—')}%")
    stop_loss = risk.get("stop_loss") or {}
    if stop_loss:
        lines.append(
            f"- **止损临近/触发**：{stop_loss.get('near_count', 0)}/{stop_loss.get('triggered_count', 0)} 件"
        )
    lines.append("")

    lines.extend(["## 3. 重点持仓（按市值）", ""])
    top_items = context.get("top_items") or []
    if top_items:
        lines.append("| 饰品 | 现价 | 盈亏 | 趋势 |")
        lines.append("| --- | --- | --- | --- |")
        for row in top_items:
            lot_note = ""
            lot_count = int(row.get("lot_count") or 0)
            if lot_count > 1:
                lot_note = f"（{lot_count} 笔合并）"
            lines.append(
                f"| {_escape_md_table_cell((row.get('item_name') or '?') + lot_note)} "
                f"| {_format_money(_safe_float(row.get('market_price')))} "
                f"| {_format_pct(_safe_float(row.get('pnl_pct')))} "
                f"| {_escape_md_table_cell(row.get('trend_status') or '—')} |"
            )
    else:
        lines.append("- 暂无持仓")
    lines.append("")

    rank_leaders = market.get("rank_leaders") or {}
    if rank_leaders:
        lines.extend(_build_rank_section(rank_leaders))

    rank_analysis = context.get("rank_analysis")
    if rank_analysis:
        lines.extend(["## 5. 涨跌幅榜解读", "", str(rank_analysis).strip(), ""])

    lines.extend([
        "",
        "*以上为系统自动生成，非投资建议；买卖决策请结合平台流动性自行判断。*",
    ])
    return "\n".join(lines)


def _build_daily_ai_prompt(context: Dict[str, Any]) -> str:
    compact = {
        "report_date": context.get("report_date"),
        "market": context.get("market"),
        "portfolio_summary": (context.get("portfolio") or {}).get("summary"),
        "risk": {
            "concentration": (context.get("risk") or {}).get("concentration"),
            "stop_loss": (context.get("risk") or {}).get("stop_loss"),
            "top_gainers": (context.get("risk") or {}).get("top_gainers"),
            "top_losers": (context.get("risk") or {}).get("top_losers"),
        },
        "top_items": context.get("top_items"),
    }
    facts = json.dumps(compact, ensure_ascii=False, indent=2)
    return (
        "你是 CS2 饰品交易助手。请基于以下结构化数据写一份中文每日复盘摘要。\n"
        "必须包含四段（用空行分隔，不要 Markdown 标题）：\n"
        "1) 今日大盘一句话\n"
        "2) 我的全仓结构与风险\n"
        "3) 建议卖出/减仓的饰品（若无则写「暂无」，仅基于持仓盈亏与止损风险事实）\n"
        "4) 建议持有/观望的饰品\n"
        "对关键数字、饰品名称、盈亏比例、止损/集中度结论使用 Markdown **加粗**。\n"
        "若提供了 market.rank_leaders，在段 1 末尾补充一句涨跌幅榜热点（仅引用给定榜单名称与涨跌幅）。\n"
        "禁止编造未提供的数据；不要罗列原始告警日志；总字数 250-500 字。\n"
        f"\n数据 JSON：\n{facts}\n"
    )


def _build_rank_analysis_prompt(context: Dict[str, Any]) -> Optional[str]:
    rank_leaders = (context.get("market") or {}).get("rank_leaders") or {}
    gainers = list(rank_leaders.get("gainers") or [])
    losers = list(rank_leaders.get("losers") or [])
    if not gainers and not losers:
        return None
    payload = json.dumps(
        {
            "day_type": rank_leaders.get("day_type"),
            "gainers": gainers,
            "losers": losers,
        },
        ensure_ascii=False,
        indent=2,
    )
    return (
        "你是 CS2 饰品市场分析助手。请基于 CSQAQ 近 7 天涨跌幅榜数据写一段中文解读（120-220 字）。\n"
        "要求：\n"
        "1) 概括涨幅榜前几名共性（品类/价位/是否小样本高波动）；\n"
        "2) 概括跌幅榜前几名风险点；\n"
        "3) 说明榜单多为全市场样本，与用户持仓无直接对应；\n"
        "4) 关键饰品名与涨跌幅用 **加粗**；不要 Markdown 标题。\n"
        f"\n榜单 JSON：\n{payload}\n"
    )


def generate_daily_ai_summary(context: Dict[str, Any], config: "Config") -> Optional[str]:
    if not getattr(config, "cs_daily_report_ai_enabled", True):
        return None
    try:
        from src.analyzer import GeminiAnalyzer

        analyzer = GeminiAnalyzer()
        if not analyzer.is_available():
            return None
        text = analyzer.generate_text(
            _build_daily_ai_prompt(context),
            max_tokens=1024,
            temperature=0.5,
        )
        return (text or "").strip() or None
    except Exception as exc:
        logger.warning("CS daily report AI summary failed: %s", exc)
        return None


def generate_rank_analysis(context: Dict[str, Any], config: "Config") -> Optional[str]:
    if not getattr(config, "cs_daily_report_ai_enabled", True):
        return None
    prompt = _build_rank_analysis_prompt(context)
    if not prompt:
        return None
    try:
        from src.analyzer import GeminiAnalyzer

        analyzer = GeminiAnalyzer()
        if not analyzer.is_available():
            return None
        text = analyzer.generate_text(prompt, max_tokens=512, temperature=0.5)
        return (text or "").strip() or None
    except Exception as exc:
        logger.warning("CS daily report rank analysis failed: %s", exc)
        return None


def run_daily_report(
    *,
    config: Optional["Config"] = None,
    notifier: Any = None,
) -> "NotificationDispatchResult":
    from src.config import get_config
    from src.notification import NotificationService

    runtime_config = config or get_config()
    context = collect_daily_context(runtime_config)
    ai_summary = generate_daily_ai_summary(context, runtime_config)
    rank_analysis = generate_rank_analysis(context, runtime_config)
    if rank_analysis:
        context["rank_analysis"] = rank_analysis
    body = build_daily_template_markdown(context, ai_summary=ai_summary)
    subject = build_daily_subject(context, runtime_config)
    notification_service = notifier or NotificationService()
    return notification_service.send_with_results(
        body,
        route_type="report",
        email_send_to_all=True,
        email_subject=subject,
    )


def maybe_run_cs_daily_report(
    *,
    config: Optional["Config"] = None,
    notifier: Any = None,
    now: Optional[datetime] = None,
) -> bool:
    """Send today's report once after the configured time. Returns True if sent."""
    global _last_sent_date

    from src.config import get_config

    runtime_config = config or get_config()
    if not getattr(runtime_config, "cs_daily_report_enabled", False):
        return False

    current = now or datetime.now()
    scheduled = _parse_hhmm(str(getattr(runtime_config, "cs_daily_report_time", "20:00")))
    if current.time() < scheduled:
        return False

    today = current.date().isoformat()
    with _last_sent_lock:
        if _last_sent_date == today:
            return False
        _last_sent_date = today

    try:
        dispatch = run_daily_report(config=runtime_config, notifier=notifier)
        if not dispatch.success:
            logger.warning("[CSDailyReport] dispatch failed: %s", dispatch.message)
            with _last_sent_lock:
                if _last_sent_date == today:
                    _last_sent_date = None
            return False
        logger.info("[CSDailyReport] daily report sent for %s", today)
        return True
    except Exception as exc:
        logger.exception("[CSDailyReport] failed: %s", exc)
        with _last_sent_lock:
            if _last_sent_date == today:
                _last_sent_date = None
        return False
