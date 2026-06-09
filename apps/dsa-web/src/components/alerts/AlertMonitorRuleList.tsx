import type React from 'react';
import { Bell, Plus } from 'lucide-react';
import type { AlertRuleBusyState, AlertRuleEnabledFilter, AlertTypeFilter } from './AlertRuleList';
import { AlertRuleMonitorCardList } from './AlertRuleMonitorCard';
import { Button, Card, EmptyState, Input, Loading, Pagination, Select } from '../common';
import type { EnrichedAlertRule } from '../../utils/csAlertMonitor';
import { cn } from '../../utils/cn';

const ENABLED_FILTER_OPTIONS = [
  { value: 'all', label: '全部状态' },
  { value: 'enabled', label: '已启用' },
  { value: 'disabled', label: '已停用' },
];

const PRIORITY_FILTER_OPTIONS = [
  { value: 'all', label: '全部优先级' },
  { value: 'urgent', label: '紧急' },
  { value: 'watch', label: '关注' },
  { value: 'normal', label: '正常' },
];

const CS_ALERT_TYPE_FILTER_OPTIONS = [
  { value: 'all', label: '全部类型' },
  { value: 'cs_price_cross', label: 'CS 价格突破' },
  { value: 'cs_pnl_threshold', label: 'CS 盈亏阈值' },
  { value: 'cs_price_stale', label: 'CS 价格状态' },
  { value: 'cs_concentration', label: 'CS 持仓集中度' },
  { value: 'cs_stop_loss', label: 'CS 持仓止损' },
];

export type AlertPriorityFilter = 'all' | 'urgent' | 'watch' | 'normal';

export type AlertScopeFilter = 'all' | 'cs_item' | 'cs_holdings';

const SCOPE_FILTER_OPTIONS = [
  { value: 'all', label: '全部范围' },
  { value: 'cs_item', label: '单品规则' },
  { value: 'cs_holdings', label: '全仓规则' },
];

type AlertMonitorRuleListProps = {
  enrichedRules: EnrichedAlertRule[];
  total: number;
  page: number;
  pageSize: number;
  isLoading?: boolean;
  enabledFilter: AlertRuleEnabledFilter;
  alertTypeFilter: AlertTypeFilter;
  scopeFilter: AlertScopeFilter;
  priorityFilter: AlertPriorityFilter;
  searchQuery: string;
  onEnabledFilterChange: (value: AlertRuleEnabledFilter) => void;
  onAlertTypeFilterChange: (value: AlertTypeFilter) => void;
  onScopeFilterChange: (value: AlertScopeFilter) => void;
  onPriorityFilterChange: (value: AlertPriorityFilter) => void;
  onSearchQueryChange: (value: string) => void;
  onPageChange: (page: number) => void;
  onCreateRule?: () => void;
  onToggleEnabled: (ruleId: number) => void;
  onDelete: (ruleId: number) => void;
  onTest: (ruleId: number) => void;
  busyRule?: AlertRuleBusyState | null;
};

export const AlertMonitorRuleList: React.FC<AlertMonitorRuleListProps> = ({
  enrichedRules,
  total,
  page,
  pageSize,
  isLoading = false,
  enabledFilter,
  alertTypeFilter,
  scopeFilter,
  priorityFilter,
  searchQuery,
  onEnabledFilterChange,
  onAlertTypeFilterChange,
  onScopeFilterChange,
  onPriorityFilterChange,
  onSearchQueryChange,
  onPageChange,
  onCreateRule,
  onToggleEnabled,
  onDelete,
  onTest,
  busyRule = null,
}) => {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const pageStart = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const pageEnd = Math.min(page * pageSize, total);
  const showPagination = total > pageSize;
  const hasClientFilters = searchQuery.trim().length > 0 || priorityFilter !== 'all';

  return (
    <Card variant="bordered" padding="sm" className="text-sm">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap items-baseline gap-1.5">
          <h3 className="text-sm font-semibold text-foreground">规则管理</h3>
          <span className="text-[11px] text-secondary-text">{total} 条 · 每页 {pageSize} 条</span>
        </div>
        {onCreateRule ? (
          <Button variant="primary" size="xsm" onClick={onCreateRule}>
            <Plus className="h-3.5 w-3.5" />
            新建规则
          </Button>
        ) : null}
      </div>
      <div className="mb-2 grid gap-1.5 sm:grid-cols-2 lg:grid-cols-4 [&_label]:mb-0.5 [&_label]:text-[11px] [&_label]:font-normal [&_select]:h-8 [&_select]:rounded-lg [&_select]:px-2.5 [&_select]:py-1 [&_select]:text-xs">
        <Select label="启停状态" value={enabledFilter} options={ENABLED_FILTER_OPTIONS} onChange={(value) => onEnabledFilterChange(value as AlertRuleEnabledFilter)} />
        <Select label="规则类型" value={alertTypeFilter} options={CS_ALERT_TYPE_FILTER_OPTIONS} onChange={(value) => onAlertTypeFilterChange(value as AlertTypeFilter)} />
        <Select label="监控范围" value={scopeFilter} options={SCOPE_FILTER_OPTIONS} onChange={(value) => onScopeFilterChange(value as AlertScopeFilter)} />
        <Select label="优先级" value={priorityFilter} options={PRIORITY_FILTER_OPTIONS} onChange={(value) => onPriorityFilterChange(value as AlertPriorityFilter)} />
      </div>
      <div className="mb-2 [&_label]:mb-0.5 [&_label]:text-[11px] [&_label]:font-normal [&_input]:h-8 [&_input]:rounded-lg [&_input]:px-2.5 [&_input]:py-1 [&_input]:text-xs">
        <Input
          label="搜索规则"
          placeholder="输入饰品名称或规则名称"
          value={searchQuery}
          onChange={(event) => onSearchQueryChange(event.target.value)}
        />
      </div>

      {isLoading && enrichedRules.length === 0 ? <Loading label="正在加载监控规则" /> : null}

      {!isLoading && enrichedRules.length === 0 ? (
        <EmptyState
          icon={<Bell className="h-6 w-6" />}
          title="暂无匹配规则"
          description="调整筛选或搜索条件，或新建/启用更多 CS 告警规则。"
        />
      ) : null}

      {enrichedRules.length > 0 ? (
        <div className={cn(isLoading && 'pointer-events-none opacity-50')}>
          <AlertRuleMonitorCardList
            items={enrichedRules}
            busyRule={busyRule}
            onToggleEnabled={onToggleEnabled}
            onDelete={onDelete}
            onTest={onTest}
          />
        </div>
      ) : null}

      {!isLoading && total > 0 ? (
        <div className="mt-2 flex flex-wrap items-center justify-between gap-2 border-t border-border/40 pt-2">
          <p className="text-[11px] text-secondary-text">
            第
            {' '}
            {page}
            /
            {totalPages}
            {' '}
            页 · 显示
            {' '}
            {pageStart}
            -
            {pageEnd}
            {' '}
            / 共
            {' '}
            {total}
            {' '}
            条
            {hasClientFilters ? ' · 搜索/优先级筛选后分页' : ''}
          </p>
          {showPagination ? (
            <Pagination
              currentPage={page}
              totalPages={totalPages}
              onPageChange={onPageChange}
              className="gap-1 [&_button]:h-7 [&_button]:min-w-[1.75rem] [&_button]:rounded-lg [&_button]:px-2 [&_button]:text-xs"
            />
          ) : null}
        </div>
      ) : null}
    </Card>
  );
};
