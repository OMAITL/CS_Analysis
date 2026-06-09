import type React from 'react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { alertsApi } from '../api/alerts';
import { csApi } from '../api/cs';
import type { ParsedApiError } from '../api/error';
import { getParsedApiError } from '../api/error';
import { AlertCreateDrawer } from '../components/alerts/AlertCreateDrawer';
import { AlertImportantRules, AlertMonitorOverview } from '../components/alerts/AlertMonitorOverview';
import { AlertMonitorRuleList, type AlertPriorityFilter, type AlertScopeFilter } from '../components/alerts/AlertMonitorRuleList';
import { AlertAiInsightPanel } from '../components/alerts/AlertRuleMonitorCard';
import { AlertRuleTestDialog } from '../components/alerts/AlertRuleTestDialog';
import type { AlertRuleBusyState, AlertRuleEnabledFilter, AlertTypeFilter } from '../components/alerts/AlertRuleList';
import type { AlertRuleFormPreset } from '../components/alerts/AlertRuleForm';
import { ApiErrorAlert, AppPage, InlineAlert } from '../components/common';
import type {
  AlertRuleCreateRequest,
  AlertRuleItem,
  AlertRuleTestResponse,
  AlertTargetScope,
  AlertTriggerItem,
} from '../types/alerts';
import {
  buildHoldingLookup,
  buildMonitorStats,
  enrichAlertRule,
  formatDistanceDisplay,
  pickImportantRulesByItem,
  pickTopInsightItem,
  priorityLabel,
  itemMonitorKey,
  ruleMatchesSearch,
  sortEnrichedRules,
  type AlertMonitorStats,
  type CsHoldingRow,
} from '../utils/csAlertMonitor';

const PAGE_SIZE = 5;
const CS_ALERTS_ONLY = true;
const API_MAX_PAGE_SIZE = 100;

async function fetchEnabledMonitorRules() {
  const baseQuery = { csOnly: CS_ALERTS_ONLY, enabled: true as const, pageSize: API_MAX_PAGE_SIZE };
  let page = 1;
  let total = 0;
  const items: AlertRuleItem[] = [];

  while (true) {
    const response = await alertsApi.listRules({ ...baseQuery, page });
    total = response.total;
    items.push(...response.items);
    if (items.length >= total || response.items.length === 0) {
      break;
    }
    page += 1;
  }

  return { items, total };
}

function enabledFilterToQuery(value: AlertRuleEnabledFilter): boolean | undefined {
  if (value === 'enabled') return true;
  if (value === 'disabled') return false;
  return undefined;
}

function alertTypeFilterToQuery(value: AlertTypeFilter): AlertRuleItem['alertType'] | undefined {
  return value === 'all' ? undefined : value;
}

function scopeFilterToQuery(value: AlertScopeFilter): AlertTargetScope | undefined {
  if (value === 'cs_item' || value === 'cs_holdings') return value;
  return undefined;
}

async function fetchAllListRules(filters: {
  enabled?: boolean;
  alertType?: AlertRuleItem['alertType'];
  targetScope?: AlertTargetScope;
}) {
  let page = 1;
  const items: AlertRuleItem[] = [];
  let total = 0;

  while (true) {
    const response = await alertsApi.listRules({
      ...filters,
      csOnly: CS_ALERTS_ONLY,
      page,
      pageSize: API_MAX_PAGE_SIZE,
    });
    total = response.total;
    items.push(...response.items);
    if (items.length >= total || response.items.length === 0) {
      break;
    }
    page += 1;
  }

  return { items, total };
}

type AlertTestDialogState = {
  ruleName: string;
  result?: AlertRuleTestResponse;
  error?: ParsedApiError;
};

const AlertsPage: React.FC = () => {
  useEffect(() => {
    document.title = '饰品投资监控 - CS 投资助手';
  }, []);

  const [rules, setRules] = useState<AlertRuleItem[]>([]);
  const [rulesTotal, setRulesTotal] = useState(0);
  const [enabledTotal, setEnabledTotal] = useState(0);
  const [rulesPage, setRulesPage] = useState(1);
  const [enabledFilter, setEnabledFilter] = useState<AlertRuleEnabledFilter>('all');
  const [alertTypeFilter, setAlertTypeFilter] = useState<AlertTypeFilter>('all');
  const [scopeFilter, setScopeFilter] = useState<AlertScopeFilter>('all');
  const [priorityFilter, setPriorityFilter] = useState<AlertPriorityFilter>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [rulesLoading, setRulesLoading] = useState(false);
  const [monitorLoading, setMonitorLoading] = useState(false);
  const [rulesError, setRulesError] = useState<ParsedApiError | null>(null);
  const [holdingsRows, setHoldingsRows] = useState<CsHoldingRow[]>([]);
  const [monitorRules, setMonitorRules] = useState<AlertRuleItem[]>([]);

  const [triggers, setTriggers] = useState<AlertTriggerItem[]>([]);

  const [drawerOpen, setDrawerOpen] = useState(false);
  const [formPreset, setFormPreset] = useState<AlertRuleFormPreset | null>(null);

  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState<ParsedApiError | null>(null);
  const [createSuccess, setCreateSuccess] = useState<string | null>(null);
  const [busyRule, setBusyRule] = useState<AlertRuleBusyState | null>(null);
  const [testDialog, setTestDialog] = useState<AlertTestDialogState | null>(null);
  const rulesRequestIdRef = useRef(0);

  const holdingLookup = useMemo(() => buildHoldingLookup(holdingsRows), [holdingsRows]);

  const filteredEnrichedRules = useMemo(() => {
    let items = sortEnrichedRules(rules.map((rule) => enrichAlertRule(rule, holdingLookup)));
    const query = searchQuery.trim();
    if (query) {
      items = items.filter((item) => ruleMatchesSearch(item, query));
    }
    if (priorityFilter !== 'all') {
      items = items.filter((item) => item.priority === priorityFilter);
    }
    return items;
  }, [rules, holdingLookup, searchQuery, priorityFilter]);

  const listTotal = filteredEnrichedRules.length;

  const enrichedPageRules = useMemo(() => {
    const start = (rulesPage - 1) * PAGE_SIZE;
    return filteredEnrichedRules.slice(start, start + PAGE_SIZE);
  }, [filteredEnrichedRules, rulesPage]);

  useEffect(() => {
    const maxPage = Math.max(1, Math.ceil(listTotal / PAGE_SIZE));
    if (rulesPage > maxPage || (listTotal > 0 && enrichedPageRules.length === 0)) {
      setRulesPage(maxPage);
    }
  }, [enrichedPageRules.length, listTotal, rulesPage]);

  const enrichedMonitorRules = useMemo(
    () => sortEnrichedRules(
      monitorRules
        .filter((rule) => rule.enabled)
        .map((rule) => enrichAlertRule(rule, holdingLookup)),
    ),
    [monitorRules, holdingLookup],
  );

  const monitorStats: AlertMonitorStats = useMemo(
    () => buildMonitorStats(rules, rulesTotal, enabledTotal, triggers, enrichedMonitorRules),
    [enabledTotal, enrichedMonitorRules, rules, rulesTotal, triggers],
  );

  const importantRules = useMemo(
    () => pickImportantRulesByItem(enrichedMonitorRules, 6).map((item) => {
      const key = itemMonitorKey(item.rule);
      const relatedCount = enrichedMonitorRules.filter(
        (candidate) => itemMonitorKey(candidate.rule) === key
          && (candidate.priority === 'urgent' || candidate.priority === 'watch'),
      ).length;
      return {
        id: item.rule.id,
        itemName: item.itemName,
        ruleTypeLabel: item.ruleTypeLabel,
        relatedCount,
        distanceDisplay: formatDistanceDisplay(item.distancePct),
        priorityLabel: priorityLabel(item.priority),
        suggestion: item.aiAdvice.suggestion,
      };
    }),
    [enrichedMonitorRules],
  );

  const topInsight = pickTopInsightItem(enrichedMonitorRules);

  const loadMonitorContext = useCallback(async () => {
    setMonitorLoading(true);
    try {
      const [enabledResp, holdingsResp] = await Promise.all([
        fetchEnabledMonitorRules(),
        csApi.getHoldingsSnapshot(false) as Promise<{ items?: CsHoldingRow[] }>,
      ]);
      setMonitorRules(enabledResp.items);
      setEnabledTotal(enabledResp.total);
      setHoldingsRows(holdingsResp.items ?? []);
    } catch (error) {
      setRulesError(getParsedApiError(error));
    } finally {
      setMonitorLoading(false);
    }
  }, []);

  const loadRules = useCallback(async () => {
    const requestId = rulesRequestIdRef.current + 1;
    rulesRequestIdRef.current = requestId;
    const isLatestRequest = () => rulesRequestIdRef.current === requestId;
    setRulesLoading(true);
    try {
      const response = await fetchAllListRules({
        enabled: enabledFilterToQuery(enabledFilter),
        alertType: alertTypeFilterToQuery(alertTypeFilter),
        targetScope: scopeFilterToQuery(scopeFilter),
      });
      if (!isLatestRequest()) return null;
      setRules(response.items);
      setRulesTotal(response.total);
      setRulesError(null);
      return response;
    } catch (error) {
      if (!isLatestRequest()) return null;
      setRulesError(getParsedApiError(error));
      return null;
    } finally {
      if (isLatestRequest()) {
        setRulesLoading(false);
      }
    }
  }, [alertTypeFilter, enabledFilter, scopeFilter]);

  const loadTriggers = useCallback(async () => {
    try {
      const response = await alertsApi.listTriggers({ page: 1, pageSize: PAGE_SIZE, csOnly: CS_ALERTS_ONLY });
      setTriggers(response.items);
    } catch {
      // 触发历史不在页面展示，静默失败不影响概览统计
    }
  }, []);

  const refreshAll = useCallback(async () => {
    await Promise.all([loadRules(), loadMonitorContext(), loadTriggers()]);
  }, [loadMonitorContext, loadRules, loadTriggers]);

  useEffect(() => {
    void loadMonitorContext();
    void loadTriggers();
  }, [loadMonitorContext, loadTriggers]);

  useEffect(() => {
    void loadRules();
  }, [loadRules]);

  const openCreateDrawer = (preset?: AlertRuleFormPreset | null) => {
    setFormPreset(preset ?? null);
    setDrawerOpen(true);
  };

  const handleCreateRule = async (payload: AlertRuleCreateRequest) => {
    setCreateLoading(true);
    setCreateError(null);
    setCreateSuccess(null);
    try {
      const created = await alertsApi.createRule(payload);
      setCreateSuccess(`已创建告警规则「${created.name}」`);
      await refreshAll();
      setRulesPage(1);
      return true;
    } catch (error) {
      setCreateError(getParsedApiError(error));
      return false;
    } finally {
      setCreateLoading(false);
    }
  };

  const findRuleById = (ruleId: number) => rules.find((rule) => rule.id === ruleId) ?? monitorRules.find((rule) => rule.id === ruleId);

  const handleToggleEnabled = async (ruleId: number) => {
    const rule = findRuleById(ruleId);
    if (!rule) return;
    setBusyRule({ id: rule.id, action: 'toggle' });
    try {
      if (rule.enabled) await alertsApi.disableRule(rule.id);
      else await alertsApi.enableRule(rule.id);
      await refreshAll();
    } catch (error) {
      setRulesError(getParsedApiError(error));
    } finally {
      setBusyRule(null);
    }
  };

  const handleDeleteRule = async (ruleId: number) => {
    setBusyRule({ id: ruleId, action: 'delete' });
    try {
      await alertsApi.deleteRule(ruleId);
      await refreshAll();
    } catch (error) {
      setRulesError(getParsedApiError(error));
    } finally {
      setBusyRule(null);
    }
  };

  const handleTestRule = async (ruleId: number) => {
    const testedRule = enrichedPageRules.find((item) => item.rule.id === ruleId);
    const ruleName = testedRule?.rule.name ?? testedRule?.itemName ?? `规则 #${ruleId}`;
    setBusyRule({ id: ruleId, action: 'test' });
    try {
      const result = await alertsApi.testRule(ruleId);
      setTestDialog({ ruleName, result });
    } catch (error) {
      setTestDialog({ ruleName, error: getParsedApiError(error) });
    } finally {
      setBusyRule(null);
    }
  };

  return (
    <AppPage className="space-y-5">
      {createError ? <ApiErrorAlert error={createError} onDismiss={() => setCreateError(null)} /> : null}
      {rulesError ? <ApiErrorAlert error={rulesError} onDismiss={() => setRulesError(null)} /> : null}
      {createSuccess ? (
        <InlineAlert
          title="操作成功"
          message={createSuccess}
          variant="success"
          action={(
            <button type="button" className="text-sm underline" onClick={() => setCreateSuccess(null)}>
              关闭
            </button>
          )}
        />
      ) : null}

      <AlertMonitorOverview stats={monitorStats} isLoading={monitorLoading || rulesLoading} />
      <AlertImportantRules items={importantRules} />
      <AlertAiInsightPanel topItem={topInsight} />

      <AlertMonitorRuleList
        enrichedRules={enrichedPageRules}
        total={listTotal}
        page={rulesPage}
        pageSize={PAGE_SIZE}
        isLoading={rulesLoading}
        enabledFilter={enabledFilter}
        alertTypeFilter={alertTypeFilter}
        scopeFilter={scopeFilter}
        priorityFilter={priorityFilter}
        searchQuery={searchQuery}
        onCreateRule={() => openCreateDrawer()}
        onEnabledFilterChange={(value) => {
          setEnabledFilter(value);
          setRulesPage(1);
        }}
        onAlertTypeFilterChange={(value) => {
          setAlertTypeFilter(value);
          setRulesPage(1);
        }}
        onScopeFilterChange={(value) => {
          setScopeFilter(value);
          setRulesPage(1);
        }}
        onPriorityFilterChange={(value) => {
          setPriorityFilter(value);
          setRulesPage(1);
        }}
        onSearchQueryChange={(value) => {
          setSearchQuery(value);
          setRulesPage(1);
        }}
        onPageChange={setRulesPage}
        onToggleEnabled={(ruleId) => void handleToggleEnabled(ruleId)}
        onDelete={(ruleId) => void handleDeleteRule(ruleId)}
        onTest={(ruleId) => void handleTestRule(ruleId)}
        busyRule={busyRule}
      />

      <AlertCreateDrawer
        isOpen={drawerOpen}
        onClose={() => {
          setDrawerOpen(false);
          setFormPreset(null);
        }}
        onSubmit={handleCreateRule}
        isSubmitting={createLoading}
        preset={formPreset}
      />

      <AlertRuleTestDialog
        isOpen={testDialog != null}
        onClose={() => setTestDialog(null)}
        ruleName={testDialog?.ruleName}
        result={testDialog?.result}
        error={testDialog?.error}
      />
    </AppPage>
  );
};

export default AlertsPage;
