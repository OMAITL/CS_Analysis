import type { AlertRuleCreateRequest, AlertRuleItem, AlertTriggerItem } from '../types/alerts';
import { formatCsItemAlertTarget } from './csAlertDisplay';

export type AlertPriority = 'urgent' | 'watch' | 'normal' | 'unknown';

export type CsHoldingRow = {
  goodId?: number | null;
  itemName?: string;
  platform?: string;
  quantity?: number;
  purchasePrice?: number;
  marketPrice?: number | null;
  pnlPct?: number | null;
};

export type CsPriceActionLabel = '止盈' | '止损';

export type CsRuleScopeLabel = '单品' | '全仓';

export type DistanceToTrigger = {
  distancePct: number | null;
  progress: number;
  isAtOrPastTarget: boolean;
  overrunPct: number | null;
};

export type EnrichedAlertRule = {
  rule: AlertRuleItem;
  itemName: string;
  ruleTypeLabel: string;
  priceActionLabel: CsPriceActionLabel | null;
  scopeLabel: CsRuleScopeLabel | null;
  displayName: string;
  targetPrice: number | null;
  currentPrice: number | null;
  distancePct: number | null;
  isAtOrPastTarget: boolean;
  overrunPct: number | null;
  progress: number;
  priority: AlertPriority;
  holding?: {
    quantity: number;
    purchasePrice: number;
    pnlPct: number | null;
  };
  aiAdvice: {
    bullets: string[];
    suggestion: string;
  };
};

export type AlertMonitorStats = {
  totalRules: number;
  enabledRules: number;
  todayTriggered: number;
  coolingRules: number;
  nearTriggerRules: number;
};

export type AlertActivityItem = {
  id: string;
  timeLabel: string;
  title: string;
  tone: 'urgent' | 'watch' | 'info' | 'neutral';
};

const TYPE_LABEL: Record<string, string> = {
  cs_price_cross: '价格突破',
  cs_stop_loss: '止损规则',
  cs_pnl_threshold: '盈亏阈值',
  cs_price_stale: '价格状态',
  cs_concentration: '持仓集中度',
};

const AUTO_PRICE_RE = /[≥≤]\s*([\d.]+)/;

export function parseCsItemGoodId(target: string): number | null {
  const parsed = Number.parseInt(target, 10);
  if (!Number.isInteger(parsed) || parsed <= 0) {
    return null;
  }
  return parsed;
}

export function holdingKey(goodId: number, platform?: string | null): string {
  return `${goodId}:${(platform ?? 'yyyp').toLowerCase()}`;
}

export function buildHoldingLookup(rows: CsHoldingRow[]): Map<string, CsHoldingRow> {
  const map = new Map<string, CsHoldingRow>();
  for (const row of rows) {
    if (!row.goodId) continue;
    map.set(holdingKey(row.goodId, row.platform), row);
  }
  return map;
}

export function resolveRuleItemName(rule: AlertRuleItem): string {
  if (rule.targetScope === 'cs_item') {
    return formatCsItemAlertTarget(rule);
  }
  if (rule.targetScope === 'cs_holdings') {
    return rule.target === 'all' ? '全部 CS 持仓' : `CS 平台 ${rule.target}`;
  }
  return rule.name;
}

export function resolveRuleScopeLabel(rule: AlertRuleItem): CsRuleScopeLabel | null {
  if (rule.targetScope === 'cs_item') return '单品';
  if (rule.targetScope === 'cs_holdings') return '全仓';
  return null;
}

export function resolveRuleDisplayName(rule: AlertRuleItem, itemName: string): string {
  if (rule.targetScope === 'cs_holdings') {
    return rule.name;
  }
  return itemName !== '单饰品' ? itemName : rule.name;
}

export function ruleMatchesSearch(item: EnrichedAlertRule, query: string): boolean {
  const normalized = query.trim().toLowerCase();
  if (!normalized) return true;
  const haystack = [
    item.displayName,
    item.itemName,
    item.rule.name,
    item.rule.target,
    item.ruleTypeLabel,
    item.priceActionLabel,
    item.scopeLabel,
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase();
  return haystack.includes(normalized);
}

export function resolveRuleTypeLabel(rule: AlertRuleItem): string {
  return TYPE_LABEL[rule.alertType] ?? rule.alertType;
}

export function resolvePriceActionLabel(rule: AlertRuleItem): CsPriceActionLabel | null {
  const name = rule.name ?? '';
  if (name.includes('自动止盈')) return '止盈';
  if (name.includes('自动止损')) return '止损';
  if (rule.alertType === 'cs_stop_loss') return '止损';
  if (rule.alertType === 'cs_price_cross') {
    if (rule.parameters.direction === 'above') return '止盈';
    if (rule.parameters.direction === 'below') return '止损';
  }
  return null;
}

export function resolveTargetPrice(rule: AlertRuleItem): number | null {
  const paramPrice = rule.parameters.price;
  if (typeof paramPrice === 'number' && Number.isFinite(paramPrice) && paramPrice > 0) {
    return paramPrice;
  }
  const match = rule.name.match(AUTO_PRICE_RE);
  if (match?.[1]) {
    const parsed = Number.parseFloat(match[1]);
    if (Number.isFinite(parsed) && parsed > 0) {
      return parsed;
    }
  }
  return null;
}

export function computeDistanceToTrigger(
  targetPrice: number | null,
  currentPrice: number | null,
  direction?: 'above' | 'below',
): DistanceToTrigger {
  if (targetPrice == null || currentPrice == null || targetPrice <= 0) {
    return { distancePct: null, progress: 0, isAtOrPastTarget: false, overrunPct: null };
  }

  if (direction === 'below') {
    if (currentPrice <= targetPrice) {
      const overrunPct = ((targetPrice - currentPrice) / targetPrice) * 100;
      return { distancePct: 0, progress: 100, isAtOrPastTarget: true, overrunPct };
    }
    const distancePct = ((currentPrice - targetPrice) / targetPrice) * 100;
    return { distancePct, progress: distanceProgress(distancePct), isAtOrPastTarget: false, overrunPct: null };
  }

  if (direction === 'above') {
    if (currentPrice >= targetPrice) {
      const overrunPct = ((currentPrice - targetPrice) / targetPrice) * 100;
      return { distancePct: 0, progress: 100, isAtOrPastTarget: true, overrunPct };
    }
    const distancePct = ((targetPrice - currentPrice) / targetPrice) * 100;
    return { distancePct, progress: distanceProgress(distancePct), isAtOrPastTarget: false, overrunPct: null };
  }

  return { distancePct: null, progress: 0, isAtOrPastTarget: false, overrunPct: null };
}

export function formatDistanceDisplay(distancePct: number | null): string {
  if (distancePct != null) {
    return `${distancePct.toFixed(1)}%`;
  }
  return '--';
}

function distanceProgress(distancePct: number): number {
  if (distancePct >= 10) return Math.max(8, 100 - distancePct * 4);
  return Math.max(0, Math.min(100, (1 - distancePct / 10) * 100));
}

export function priorityFromDistance(distancePct: number | null): AlertPriority {
  if (distancePct == null) return 'unknown';
  if (distancePct < 3) return 'urgent';
  if (distancePct < 10) return 'watch';
  return 'normal';
}

export function priorityRank(priority: AlertPriority): number {
  if (priority === 'urgent') return 0;
  if (priority === 'watch') return 1;
  if (priority === 'normal') return 2;
  return 3;
}

export function buildAiAdvice(
  rule: AlertRuleItem,
  itemName: string,
  distancePct: number | null,
  holding?: EnrichedAlertRule['holding'],
  distanceMeta?: Pick<DistanceToTrigger, 'isAtOrPastTarget' | 'overrunPct'>,
): EnrichedAlertRule['aiAdvice'] {
  const bullets: string[] = [];
  let suggestion = '继续持有';

  const direction = rule.parameters.direction;
  if (distanceMeta?.isAtOrPastTarget && distanceMeta.overrunPct != null) {
    if (direction === 'below') {
      bullets.push(`已跌破止损线 ${distanceMeta.overrunPct.toFixed(1)}%`);
      suggestion = '亏损扩大，优先控风险';
    } else if (direction === 'above') {
      bullets.push(`已超过止盈目标 ${distanceMeta.overrunPct.toFixed(1)}%`);
      suggestion = '可考虑分批止盈';
    }
  } else if (distancePct != null) {
    if (direction === 'below') {
      bullets.push(`当前价格距离止损位仅剩 ${distancePct.toFixed(1)}%`);
      if (distancePct < 3) suggestion = '减仓观察';
      else if (distancePct < 10) suggestion = '收紧止损，留意回落';
    } else if (direction === 'above') {
      bullets.push(`距离止盈目标还有 ${distancePct.toFixed(1)}%`);
      if (distancePct < 3) suggestion = '可考虑分批止盈';
      else if (distancePct < 10) suggestion = '接近目标，保持关注';
    }
  }

  if (holding?.pnlPct != null) {
    bullets.push(`持仓浮盈 ${holding.pnlPct >= 0 ? '+' : ''}${holding.pnlPct.toFixed(1)}%`);
    if (holding.pnlPct <= -8) suggestion = '亏损扩大，优先控风险';
    if (holding.pnlPct >= 20 && suggestion === '继续持有') {
      if (direction === 'above') {
        suggestion = '盈利较好，可考虑锁定部分利润';
      } else if (direction === 'below') {
        suggestion = '盈利中，价格仍高于止损线，可继续观察';
      } else {
        suggestion = '盈利较好，可考虑锁定部分利润';
      }
    }
  }

  if (rule.alertType === 'cs_stop_loss') {
    bullets.push('规则监控持仓整体止损状态');
    if (suggestion === '继续持有') suggestion = '关注持仓回撤';
  }

  if (bullets.length === 0) {
    bullets.push(`${itemName} 规则运行正常`);
  }

  return { bullets, suggestion };
}

export function enrichAlertRule(rule: AlertRuleItem, holdings: Map<string, CsHoldingRow>): EnrichedAlertRule {
  const itemName = resolveRuleItemName(rule);
  const targetPrice = resolveTargetPrice(rule);
  let currentPrice: number | null = null;
  let holdingInfo: EnrichedAlertRule['holding'];

  if (rule.targetScope === 'cs_item') {
    const goodId = parseCsItemGoodId(rule.target);
    const platform = rule.parameters.platform ?? 'yyyp';
    if (goodId) {
      const row = holdings.get(holdingKey(goodId, platform));
      if (row?.marketPrice != null) {
        currentPrice = row.marketPrice;
      }
      if (row) {
        holdingInfo = {
          quantity: row.quantity ?? 1,
          purchasePrice: row.purchasePrice ?? 0,
          pnlPct: row.pnlPct ?? null,
        };
      }
    }
  }

  const priceDirection = rule.parameters.direction === 'above' || rule.parameters.direction === 'below'
    ? rule.parameters.direction
    : undefined;
  const distanceMeta = computeDistanceToTrigger(
    targetPrice,
    currentPrice,
    priceDirection,
  );
  const { distancePct, progress, isAtOrPastTarget, overrunPct } = distanceMeta;
  const priority = rule.enabled && !rule.cooldownActive ? priorityFromDistance(distancePct) : 'unknown';

  const priceActionLabel = resolvePriceActionLabel(rule);
  const scopeLabel = resolveRuleScopeLabel(rule);

  return {
    rule,
    itemName,
    displayName: resolveRuleDisplayName(rule, itemName),
    ruleTypeLabel: priceActionLabel ?? resolveRuleTypeLabel(rule),
    priceActionLabel,
    scopeLabel,
    targetPrice,
    currentPrice,
    distancePct,
    isAtOrPastTarget,
    overrunPct,
    progress,
    priority,
    holding: holdingInfo,
    aiAdvice: buildAiAdvice(rule, itemName, distancePct, holdingInfo, distanceMeta),
  };
}

export function itemMonitorKey(rule: AlertRuleItem): string {
  if (rule.targetScope === 'cs_item') {
    const platform = rule.parameters.platform ?? 'yyyp';
    return `cs_item:${rule.target}:${platform}`;
  }
  if (rule.targetScope === 'cs_holdings') {
    return `cs_holdings:${rule.target ?? 'all'}`;
  }
  return `rule:${rule.id}`;
}

/** 顶部 AI 建议：优先展示已触发、且与当前盈亏更相关的规则（如同一饰品的止盈）。 */
export function pickTopInsightItem(items: EnrichedAlertRule[]): EnrichedAlertRule | null {
  const enabled = items.filter((item) => item.rule.enabled);
  if (enabled.length === 0) return null;

  const breached = enabled.filter((item) => item.isAtOrPastTarget);
  if (breached.length > 0) {
    return [...breached].sort((a, b) => {
      const dirA = a.rule.parameters.direction === 'above' ? 0 : 1;
      const dirB = b.rule.parameters.direction === 'above' ? 0 : 1;
      if (dirA !== dirB) return dirA - dirB;
      return (b.overrunPct ?? 0) - (a.overrunPct ?? 0);
    })[0];
  }

  const important = pickImportantRulesByItem(enabled, 1);
  if (important.length > 0) return important[0];

  const profitable = enabled.filter((item) => (item.holding?.pnlPct ?? 0) >= 20);
  const takeProfitCandidates = profitable.filter((item) => item.priceActionLabel === '止盈');
  if (takeProfitCandidates.length > 0) {
    return sortEnrichedRules(takeProfitCandidates)[0];
  }

  return sortEnrichedRules(enabled)[0] ?? null;
}

/** 顶部横幅：标签与建议语义冲突时不展示止盈/止损 badge，避免误导。 */
export function shouldShowInsightPriceBadge(item: EnrichedAlertRule): boolean {
  const { priceActionLabel, aiAdvice, holding } = item;
  if (!priceActionLabel) return false;

  const profitOriented = /锁定|止盈/.test(aiAdvice.suggestion);
  const riskOriented = /控风险|亏损扩大|减仓/.test(aiAdvice.suggestion);

  if (priceActionLabel === '止损' && profitOriented) return false;
  if (priceActionLabel === '止盈' && holding?.pnlPct != null && holding.pnlPct < -5 && riskOriented) {
    return false;
  }
  return true;
}

/** 同一饰品可能有多条规则（止损+止盈等），重要告警按饰品去重，保留距离最近的一条。 */
export function pickImportantRulesByItem(items: EnrichedAlertRule[], limit = 6): EnrichedAlertRule[] {
  const byItem = new Map<string, EnrichedAlertRule>();

  for (const item of items) {
    if (item.priority !== 'urgent' && item.priority !== 'watch') continue;
    const key = itemMonitorKey(item.rule);
    const existing = byItem.get(key);
    if (!existing) {
      byItem.set(key, item);
      continue;
    }
    const distA = item.distancePct ?? Number.POSITIVE_INFINITY;
    const distB = existing.distancePct ?? Number.POSITIVE_INFINITY;
    if (distA < distB || (distA === distB && priorityRank(item.priority) < priorityRank(existing.priority))) {
      byItem.set(key, item);
    }
  }

  return sortEnrichedRules([...byItem.values()]).slice(0, limit);
}

export function countNearTriggerItems(items: EnrichedAlertRule[]): number {
  const keys = new Set<string>();
  for (const item of items) {
    if (item.priority !== 'urgent' && item.priority !== 'watch') continue;
    keys.add(itemMonitorKey(item.rule));
  }
  return keys.size;
}

export function sortEnrichedRules(items: EnrichedAlertRule[]): EnrichedAlertRule[] {
  return [...items].sort((a, b) => {
    const rankDiff = priorityRank(a.priority) - priorityRank(b.priority);
    if (rankDiff !== 0) return rankDiff;
    const distA = a.distancePct ?? Number.POSITIVE_INFINITY;
    const distB = b.distancePct ?? Number.POSITIVE_INFINITY;
    if (distA !== distB) return distA - distB;
    return (b.rule.updatedAt ?? '').localeCompare(a.rule.updatedAt ?? '');
  });
}

export function buildMonitorStats(
  rules: AlertRuleItem[],
  totalRules: number,
  enabledTotal: number,
  triggers: AlertTriggerItem[],
  enrichedEnabled: EnrichedAlertRule[],
): AlertMonitorStats {
  const today = new Date();
  const todayKey = today.toISOString().slice(0, 10);
  const todayTriggered = triggers.filter((item) => {
    if (item.status !== 'triggered') return false;
    const stamp = item.triggeredAt ?? item.dataTimestamp;
    return stamp?.slice(0, 10) === todayKey;
  }).length;

  const coolingRules = rules.filter((rule) => rule.cooldownActive).length;
  const nearTriggerRules = countNearTriggerItems(enrichedEnabled);

  return {
    totalRules,
    enabledRules: enabledTotal,
    todayTriggered,
    coolingRules,
    nearTriggerRules,
  };
}

function formatTimeLabel(value?: string | null): string {
  if (!value) return '--:--';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '--:--';
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false });
}

function isToday(value?: string | null): boolean {
  if (!value) return false;
  return value.slice(0, 10) === new Date().toISOString().slice(0, 10);
}

function aggregateRuleCreationActivity(items: AlertActivityItem[]): AlertActivityItem[] {
  const result: AlertActivityItem[] = [];
  let index = 0;

  while (index < items.length) {
    const current = items[index];
    const isRuleCreation = current.title.startsWith('新增规则：');
    if (!isRuleCreation) {
      result.push(current);
      index += 1;
      continue;
    }

    let end = index + 1;
    while (
      end < items.length
      && items[end].timeLabel === current.timeLabel
      && items[end].title.startsWith('新增规则：')
    ) {
      end += 1;
    }

    const count = end - index;
    if (count > 1) {
      result.push({
        id: `rule-batch-${current.timeLabel}-${index}`,
        timeLabel: current.timeLabel,
        title: `批量新增 ${count} 条监控规则`,
        tone: 'info',
      });
    } else {
      result.push(current);
    }
    index = end;
  }

  return result;
}

export function buildTodayActivity(
  triggers: AlertTriggerItem[],
  rules: AlertRuleItem[],
): AlertActivityItem[] {
  const items: AlertActivityItem[] = [];

  for (const trigger of triggers) {
    if (!isToday(trigger.triggeredAt ?? trigger.dataTimestamp)) continue;
    const tone = trigger.status === 'triggered' ? 'urgent' : trigger.status === 'degraded' ? 'watch' : 'neutral';
    items.push({
      id: `trigger-${trigger.id}`,
      timeLabel: formatTimeLabel(trigger.triggeredAt ?? trigger.dataTimestamp),
      title: trigger.reason ?? `${trigger.target} ${trigger.status}`,
      tone,
    });
  }

  for (const rule of rules) {
    if (!isToday(rule.createdAt)) continue;
    items.push({
      id: `rule-${rule.id}-created`,
      timeLabel: formatTimeLabel(rule.createdAt),
      title: `新增规则：${rule.name}`,
      tone: 'info',
    });
  }

  const sorted = items.sort((a, b) => {
    const timeCompare = b.timeLabel.localeCompare(a.timeLabel);
    if (timeCompare !== 0) return timeCompare;
    const aIsTrigger = a.id.startsWith('trigger-');
    const bIsTrigger = b.id.startsWith('trigger-');
    if (aIsTrigger && !bIsTrigger) return -1;
    if (!aIsTrigger && bIsTrigger) return 1;
    return 0;
  });

  return aggregateRuleCreationActivity(sorted);
}

export type AlertRuleTemplate = {
  id: string;
  label: string;
  description: string;
  preset: AlertRuleCreateRequest;
};

export const CS_ALERT_RULE_TEMPLATES: AlertRuleTemplate[] = [
  {
    id: 'breach_cost',
    label: '跌破成本价',
    description: '持仓整体跌破成本时提醒',
    preset: {
      name: '持仓跌破成本',
      targetScope: 'cs_holdings',
      target: 'all',
      alertType: 'cs_stop_loss',
      parameters: { mode: 'breach' },
      severity: 'warning',
    },
  },
  {
    id: 'gain_20',
    label: '上涨20%止盈',
    description: '持仓盈利达到 20%',
    preset: {
      name: '持仓上涨20%止盈',
      targetScope: 'cs_holdings',
      target: 'all',
      alertType: 'cs_pnl_threshold',
      parameters: { direction: 'gain', thresholdPct: 20 },
      severity: 'info',
    },
  },
  {
    id: 'gain_50',
    label: '上涨50%止盈',
    description: '持仓盈利达到 50%',
    preset: {
      name: '持仓上涨50%止盈',
      targetScope: 'cs_holdings',
      target: 'all',
      alertType: 'cs_pnl_threshold',
      parameters: { direction: 'gain', thresholdPct: 50 },
      severity: 'warning',
    },
  },
  {
    id: 'near_stop',
    label: '接近止损',
    description: '持仓接近止损线',
    preset: {
      name: '持仓接近止损',
      targetScope: 'cs_holdings',
      target: 'all',
      alertType: 'cs_stop_loss',
      parameters: { mode: 'near' },
      severity: 'warning',
    },
  },
  {
    id: 'price_stale',
    label: '价格状态异常',
    description: '饰品价格长时间未更新',
    preset: {
      name: 'CS 价格状态监控',
      targetScope: 'cs_holdings',
      target: 'all',
      alertType: 'cs_price_stale',
      parameters: {},
      severity: 'info',
    },
  },
  {
    id: 'concentration',
    label: '持仓集中度过高',
    description: '单一饰品占比过高',
    preset: {
      name: 'CS 持仓集中度',
      targetScope: 'cs_holdings',
      target: 'all',
      alertType: 'cs_concentration',
      parameters: {},
      severity: 'warning',
    },
  },
];

export function priorityLabel(priority: AlertPriority): string {
  if (priority === 'urgent') return '紧急';
  if (priority === 'watch') return '关注';
  if (priority === 'normal') return '正常';
  return '待评估';
}

export function priorityTone(priority: AlertPriority): 'danger' | 'warning' | 'success' | 'default' {
  if (priority === 'urgent') return 'danger';
  if (priority === 'watch') return 'warning';
  if (priority === 'normal') return 'success';
  return 'default';
}
