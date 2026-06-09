import type React from 'react';
import { useState } from 'react';
import { ChevronRight, Sparkles, Trash2 } from 'lucide-react';
import { Badge, Button, ConfirmDialog, StatusDot } from '../common';
import type { AlertRuleBusyState } from './AlertRuleList';
import { formatDistanceDisplay, shouldShowInsightPriceBadge, type EnrichedAlertRule } from '../../utils/csAlertMonitor';
import { formatDateTime } from '../../utils/format';
import { cn } from '../../utils/cn';

type AlertRuleMonitorCardProps = {
  item: EnrichedAlertRule;
  busyRule?: AlertRuleBusyState | null;
  expanded: boolean;
  onToggleExpand: () => void;
  onToggleEnabled: () => void;
  onDelete: () => void;
  onTest: () => void;
};

function formatMoney(value: number | null): string {
  if (value == null || !Number.isFinite(value)) return '--';
  return value.toFixed(2);
}

function priorityDotTone(priority: EnrichedAlertRule['priority']): 'danger' | 'warning' | 'success' | 'neutral' {
  if (priority === 'urgent') return 'danger';
  if (priority === 'watch') return 'warning';
  if (priority === 'normal') return 'success';
  return 'neutral';
}

function MetricCell({
  value,
  className,
}: {
  value: React.ReactNode;
  className?: string;
}) {
  return (
    <td className={cn('whitespace-nowrap px-2 py-2 tabular-nums', className)}>
      {value}
    </td>
  );
}

export const AlertRuleMonitorRow: React.FC<AlertRuleMonitorCardProps> = ({
  item,
  busyRule,
  expanded,
  onToggleExpand,
  onToggleEnabled,
  onDelete,
  onTest,
}) => {
  const {
    rule,
    displayName,
    priceActionLabel,
    scopeLabel,
    targetPrice,
    currentPrice,
    distancePct,
    holding,
    aiAdvice,
  } = item;
  const distanceText = formatDistanceDisplay(distancePct);
  const isBusy = busyRule?.id === rule.id;
  const distanceLabel = priceActionLabel ? `距${priceActionLabel}` : '距触发';
  const isPortfolioRule = rule.targetScope === 'cs_holdings';
  const pnlText = holding?.pnlPct == null
    ? '--'
    : `${holding.pnlPct >= 0 ? '+' : ''}${holding.pnlPct.toFixed(1)}%`;

  return (
    <>
      <tr
        className={cn(
          'group border-b border-border/30 transition-colors last:border-b-0 hover:bg-hover/35',
          !rule.enabled && 'opacity-60',
          expanded && 'bg-hover/25',
        )}
      >
        <td className="max-w-[220px] px-2 py-2">
          <button
            type="button"
            className="flex w-full min-w-0 items-center gap-1.5 text-left"
            onClick={onToggleExpand}
            aria-expanded={expanded}
          >
            <ChevronRight className={cn('h-3.5 w-3.5 shrink-0 text-secondary-text transition-transform', expanded && 'rotate-90')} />
            <StatusDot tone={priorityDotTone(item.priority)} className="h-2 w-2" aria-label={item.priority} />
            <span className="min-w-0 flex-1 truncate text-xs font-medium text-foreground">{displayName}</span>
            {scopeLabel ? (
              <Badge
                size="sm"
                variant={scopeLabel === '全仓' ? 'history' : 'info'}
                className="shrink-0 px-1.5 py-0 text-[10px]"
              >
                {scopeLabel}
              </Badge>
            ) : null}
            {priceActionLabel ? (
              <Badge
                size="sm"
                variant={priceActionLabel === '止盈' ? 'success' : 'danger'}
                className="shrink-0 px-1.5 py-0 text-[10px]"
              >
                {priceActionLabel}
              </Badge>
            ) : null}
          </button>
        </td>
        <MetricCell
          value={isPortfolioRule ? '--' : (currentPrice != null ? `¥${formatMoney(currentPrice)}` : '--')}
          className="font-medium text-cyan"
        />
        <MetricCell
          value={isPortfolioRule || !holding ? '--' : `¥${formatMoney(holding.purchasePrice)}`}
          className="text-xs text-secondary-text"
        />
        <MetricCell
          value={isPortfolioRule ? '--' : (targetPrice != null ? `¥${formatMoney(targetPrice)}` : '--')}
          className={cn(
            'text-xs',
            !isPortfolioRule && priceActionLabel === '止盈' && 'text-success',
            !isPortfolioRule && priceActionLabel === '止损' && 'text-danger',
          )}
        />
        <MetricCell
          value={isPortfolioRule ? (
            <span className="text-[11px] text-secondary-text">全仓监控</span>
          ) : (
            <span className="inline-flex flex-col leading-tight">
              {priceActionLabel ? (
                <span className="text-[10px] text-secondary-text/80">{distanceLabel}</span>
              ) : null}
              <span>{distanceText}</span>
            </span>
          )}
          className={cn(
            !isPortfolioRule && item.priority === 'urgent' && 'font-semibold text-danger',
            !isPortfolioRule && item.priority === 'watch' && 'font-medium text-warning',
            !isPortfolioRule && item.priority === 'normal' && 'text-secondary-text',
          )}
        />
        <MetricCell
          value={pnlText}
          className={cn(
            holding?.pnlPct != null && holding.pnlPct >= 20 && 'font-medium text-success',
            holding?.pnlPct != null && holding.pnlPct <= -10 && 'font-medium text-danger',
            holding?.pnlPct != null && holding.pnlPct > -10 && holding.pnlPct < 20 && 'text-secondary-text',
          )}
        />
        <td className="whitespace-nowrap px-2 py-2 text-right">
          <div className="inline-flex items-center gap-0.5 opacity-80 transition-opacity group-hover:opacity-100">
            <Button
              size="xsm"
              variant="ghost"
              onClick={onTest}
              isLoading={isBusy && busyRule?.action === 'test'}
              disabled={isBusy && busyRule?.action !== 'test'}
            >
              测试
            </Button>
            <Button
              size="xsm"
              variant="ghost"
              onClick={onToggleEnabled}
              isLoading={isBusy && busyRule?.action === 'toggle'}
              disabled={isBusy && busyRule?.action !== 'toggle'}
            >
              {rule.enabled ? '停用' : '启用'}
            </Button>
            <Button
              size="xsm"
              variant="ghost"
              onClick={onDelete}
              disabled={isBusy}
              aria-label={`删除 ${rule.name}`}
              className="text-danger hover:text-danger"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </Button>
          </div>
        </td>
      </tr>
      {expanded ? (
        <tr className="border-b border-border/30 bg-elevated/20 last:border-b-0">
          <td colSpan={7} className="px-3 py-2 text-[11px] leading-relaxed text-secondary-text">
            <div className="flex flex-wrap gap-x-3 gap-y-1">
              <span>
                {distanceLabel}
                {distanceText === '--' ? ' --' : ` ${distanceText}`}
              </span>
              {targetPrice != null ? <span>目标 ¥{formatMoney(targetPrice)}</span> : null}
              {holding ? (
                <span>
                  持仓
                  {holding.quantity}
                  件 · 购入 ¥
                  {formatMoney(holding.purchasePrice)}
                </span>
              ) : null}
              <span>{rule.enabled ? '已启用' : '已停用'}</span>
              <span>{formatDateTime(rule.updatedAt ?? rule.createdAt)}</span>
            </div>
            <p className="mt-1 text-foreground/90">{aiAdvice.suggestion}</p>
            <p className="mt-0.5 text-secondary-text/80">{rule.name}</p>
          </td>
        </tr>
      ) : null}
    </>
  );
};

type AlertRuleMonitorCardListProps = {
  items: EnrichedAlertRule[];
  busyRule?: AlertRuleBusyState | null;
  onToggleEnabled: (ruleId: number) => void;
  onDelete: (ruleId: number) => void;
  onTest: (ruleId: number) => void;
};

export const AlertRuleMonitorCardList: React.FC<AlertRuleMonitorCardListProps> = ({
  items,
  busyRule,
  onToggleEnabled,
  onDelete,
  onTest,
}) => {
  const [pendingDeleteId, setPendingDeleteId] = useState<number | null>(null);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const pendingItem = items.find((item) => item.rule.id === pendingDeleteId);

  return (
    <>
      <div className="overflow-x-auto rounded-lg border border-border/40">
        <table className="w-full min-w-[860px] border-collapse">
          <thead>
            <tr className="border-b border-border/40 bg-elevated/30 text-[11px] text-secondary-text">
              <th className="px-2 py-1.5 text-left font-normal">规则</th>
              <th className="px-2 py-1.5 text-left font-normal">现价</th>
              <th className="px-2 py-1.5 text-left font-normal">购入价</th>
              <th className="px-2 py-1.5 text-left font-normal">目标价</th>
              <th className="px-2 py-1.5 text-left font-normal">距目标</th>
              <th className="px-2 py-1.5 text-left font-normal" title="相对购入成本（单价×数量）">
                盈亏
              </th>
              <th className="px-2 py-1.5 text-right font-normal">操作</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <AlertRuleMonitorRow
                key={item.rule.id}
                item={item}
                busyRule={busyRule}
                expanded={expandedId === item.rule.id}
                onToggleExpand={() => setExpandedId((current) => (current === item.rule.id ? null : item.rule.id))}
                onToggleEnabled={() => onToggleEnabled(item.rule.id)}
                onDelete={() => setPendingDeleteId(item.rule.id)}
                onTest={() => onTest(item.rule.id)}
              />
            ))}
          </tbody>
        </table>
      </div>
      <ConfirmDialog
        isOpen={pendingDeleteId != null}
        title="删除告警规则"
        message={pendingItem ? `确认删除「${pendingItem.rule.name}」吗？` : ''}
        confirmText="删除"
        cancelText="取消"
        isDanger
        onConfirm={() => {
          if (pendingDeleteId != null) onDelete(pendingDeleteId);
          setPendingDeleteId(null);
        }}
        onCancel={() => setPendingDeleteId(null)}
      />
    </>
  );
};

export const AlertAiInsightPanel: React.FC<{ topItem: EnrichedAlertRule | null }> = ({ topItem }) => {
  if (!topItem) return null;
  return (
    <section className="rounded-xl border border-cyan/20 bg-gradient-to-br from-cyan/10 via-card/80 to-card/80 px-4 py-3">
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <Sparkles className="h-4 w-4 shrink-0 text-cyan" />
        <span className="font-semibold text-foreground">当前最需要关注：</span>
        <span className="font-medium text-foreground">{topItem.itemName}</span>
        {shouldShowInsightPriceBadge(topItem) && topItem.priceActionLabel ? (
          <Badge
            size="sm"
            variant={topItem.priceActionLabel === '止盈' ? 'success' : 'danger'}
            className="px-1.5 py-0 text-[10px]"
          >
            {topItem.priceActionLabel}
          </Badge>
        ) : null}
        {shouldShowInsightPriceBadge(topItem) && topItem.priceActionLabel ? (
          <span className="text-secondary-text">·</span>
        ) : null}
        <span className="text-secondary-text">{topItem.aiAdvice.suggestion}</span>
      </div>
    </section>
  );
};
