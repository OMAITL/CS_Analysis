import type React from 'react';
import { Activity, BellRing, Flame, PauseCircle, ShieldCheck, Target } from 'lucide-react';
import { StatCard } from '../common';
import type { AlertMonitorStats } from '../../utils/csAlertMonitor';

type AlertMonitorOverviewProps = {
  stats: AlertMonitorStats;
  isLoading?: boolean;
};

export const AlertMonitorOverview: React.FC<AlertMonitorOverviewProps> = ({ stats, isLoading = false }) => (
  <section aria-label="今日监控概览" className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
    <StatCard label="规则总数" value={isLoading ? '—' : stats.totalRules} icon={<BellRing className="h-5 w-5" />} />
    <StatCard
      label="已启用"
      value={isLoading ? '—' : stats.enabledRules}
      tone="success"
      icon={<ShieldCheck className="h-5 w-5" />}
    />
    <StatCard
      label="今日触发"
      value={isLoading ? '—' : stats.todayTriggered}
      tone={stats.todayTriggered > 0 ? 'warning' : 'default'}
      icon={<Activity className="h-5 w-5" />}
    />
    <StatCard
      label="冷却中"
      value={isLoading ? '—' : stats.coolingRules}
      tone="default"
      icon={<PauseCircle className="h-5 w-5" />}
    />
    <StatCard
      label="接近触发"
      value={isLoading ? '—' : stats.nearTriggerRules}
      tone={stats.nearTriggerRules > 0 ? 'danger' : 'primary'}
      icon={<Target className="h-5 w-5" />}
      hint={stats.nearTriggerRules > 0 ? '优先查看下方紧急/关注规则' : '当前暂无临近触发项'}
    />
  </section>
);

type AlertImportantRulesProps = {
  items: Array<{
    id: number;
    itemName: string;
    ruleTypeLabel: string;
    relatedCount: number;
    distanceDisplay: string;
    priorityLabel: string;
    suggestion: string;
  }>;
};

export const AlertImportantRules: React.FC<AlertImportantRulesProps> = ({ items }) => {
  if (items.length === 0) return null;

  return (
    <section aria-label="重要告警" className="rounded-2xl border border-danger/15 bg-danger/5 p-4">
      <div className="mb-3 flex items-center gap-2">
        <Flame className="h-4 w-4 text-danger" />
        <h2 className="text-sm font-semibold text-foreground">重要告警</h2>
        <span className="text-xs text-secondary-text">同一饰品仅展示最接近触发的一条</span>
      </div>
      <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-3">
        {items.map((item) => (
          <div key={item.id} className="rounded-xl border border-border/60 bg-card/80 p-3">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <p className="truncate font-medium text-foreground">{item.itemName}</p>
                <p className="mt-1 text-xs text-secondary-text">
                  {item.priorityLabel}
                  {' · '}
                  {item.ruleTypeLabel}
                  {item.relatedCount > 1 ? ` · 另有 ${item.relatedCount - 1} 条规则` : ''}
                </p>
              </div>
              {item.distanceDisplay !== '--' ? (
                <span className="shrink-0 font-mono text-sm font-semibold text-danger">
                  {item.distanceDisplay}
                </span>
              ) : null}
            </div>
            <p className="mt-2 text-xs text-secondary-text">{item.suggestion}</p>
          </div>
        ))}
      </div>
    </section>
  );
};
