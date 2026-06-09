import type React from 'react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Camera,
  Package,
  Plus,
  RefreshCw,
  Trash2,
  TrendingDown,
  TrendingUp,
  Upload,
  Wallet,
} from 'lucide-react';
import { csApi } from '../api/cs';
import {
  ApiErrorAlert,
  Badge,
  Button,
  EmptyState,
  SectionCard,
  StatCard,
} from '../components/common';
import { CsItemSearchInput } from '../components/cs/CsItemSearchInput';
import { getParsedApiError, type ParsedApiError } from '../api/error';
import { cn } from '../utils/cn';
import { displayHoldingsTitle, displayHoldingsWear } from '../utils/csHoldingsDisplay';
import type { CsGoodIdItem } from '../types/cs';
import '../styles/ia-v2.css';

type HoldingRow = {
  id: number;
  goodId?: number | null;
  itemName: string;
  wear?: string;
  platform?: string;
  quantity?: number;
  purchasePrice?: number;
  marketPrice?: number | null;
  costTotal?: number;
  marketTotal?: number | null;
  pnl?: number | null;
  pnlPct?: number | null;
  thumbnailUrl?: string | null;
};

type HoldingsSummary = {
  itemCount?: number;
  rowCount?: number;
  totalMarketValue?: number | null;
  totalCost?: number;
  totalPnl?: number | null;
};

type ExtractedItem = {
  draftId: string;
  checked: boolean;
  itemName: string;
  wear?: string;
  floatValue?: number | null;
  platform?: string;
  marketPrice?: number | null;
  purchasePrice?: number | null;
  pnl?: number | null;
  visionConfidence?: string;
  matchConfidence?: string;
  matchTier?: string;
  goodId?: number | null;
  duplicateOf?: number | null;
};

const WEAR_OPTIONS = ['崭新出厂', '略有磨损', '久经沙场', '破损不堪', '战痕累累'];

function draftFromApi(row: Record<string, unknown>): ExtractedItem {
  return {
    draftId: String(row.draftId ?? ''),
    checked: Boolean(row.checked ?? true),
    itemName: String(row.itemName ?? ''),
    wear: String(row.wear ?? ''),
    floatValue: row.floatValue as number | null | undefined,
    platform: String(row.platform ?? 'yyyp'),
    marketPrice: row.marketPrice as number | null | undefined,
    purchasePrice: row.purchasePrice as number | null | undefined,
    visionConfidence: String(row.visionConfidence ?? 'medium'),
    matchConfidence: String(row.matchConfidence ?? 'low'),
    matchTier: String(row.matchTier ?? 'none'),
    goodId: row.goodId as number | null | undefined,
    duplicateOf: row.duplicateOf as number | null | undefined,
  };
}

function draftsToApiPayload(drafts: ExtractedItem[]) {
  return drafts.map((row) => ({
    draft_id: row.draftId,
    item_name: row.itemName,
    wear: row.wear ?? '',
    float_value: row.floatValue ?? null,
    platform: row.platform ?? 'yyyp',
    purchase_price: row.purchasePrice ?? 0,
    market_price: row.marketPrice ?? null,
    good_id: row.goodId ?? null,
    checked: row.checked,
    vision_confidence: row.visionConfidence ?? 'medium',
    match_confidence: row.matchConfidence ?? 'low',
    match_tier: row.matchTier ?? 'none',
  }));
}

const FIELD_CLASS =
  'input-surface input-focus-glow h-11 w-full rounded-xl border bg-transparent px-4 text-sm transition-all focus:outline-none disabled:cursor-not-allowed disabled:opacity-60';

function formatMoney(value?: number | null, currency = '¥'): string {
  if (value == null || Number.isNaN(value)) return '--';
  return `${currency}${value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatPnl(value?: number | null): string {
  if (value == null || Number.isNaN(value)) return '--';
  const prefix = value > 0 ? '+' : '';
  return `${prefix}${formatMoney(value, '¥')}`;
}

/** A 股配色：盈利红、亏损绿 */
function pnlTone(value?: number | null): 'success' | 'danger' | 'default' {
  if (value == null || Number.isNaN(value)) return 'default';
  return value >= 0 ? 'danger' : 'success';
}

const CsHoldingsPage: React.FC = () => {
  const [summary, setSummary] = useState<HoldingsSummary>({});
  const [items, setItems] = useState<HoldingRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<ParsedApiError | null>(null);
  const [mode, setMode] = useState<'list' | 'manual' | 'image'>('list');
  const [sortKey, setSortKey] = useState<'market' | 'purchase' | 'pnl'>('market');

  const [manualName, setManualName] = useState('');
  const [manualWear, setManualWear] = useState('');
  const [manualPurchase, setManualPurchase] = useState('');
  const [manualPlatform, setManualPlatform] = useState('yyyp');
  const [selectedItem, setSelectedItem] = useState<CsGoodIdItem | null>(null);
  const [saving, setSaving] = useState(false);

  const [extracted, setExtracted] = useState<ExtractedItem[]>([]);
  const [importSessionId, setImportSessionId] = useState<string | null>(null);
  const [skipDuplicates, setSkipDuplicates] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [rematching, setRematching] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const rematchTimerRef = useRef<number | null>(null);

  const loadSnapshot = useCallback(async (refreshPrices = true) => {
    setError(null);
    try {
      const data = await csApi.getHoldingsSnapshot(refreshPrices) as {
        summary?: HoldingsSummary;
        items?: HoldingRow[];
      };
      setSummary(data.summary ?? {});
      setItems(data.items ?? []);
    } catch (err) {
      setError(getParsedApiError(err));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    document.title = '饰品持仓 - CS 投资助手';
    void loadSnapshot(true);
  }, [loadSnapshot]);

  const sortedItems = useMemo(() => {
    const rows = [...items];
    rows.sort((a, b) => {
      const pick = (row: HoldingRow) => {
        if (sortKey === 'purchase') return row.purchasePrice ?? 0;
        if (sortKey === 'pnl') return row.pnl ?? -Infinity;
        return row.marketPrice ?? 0;
      };
      return pick(b) - pick(a);
    });
    return rows;
  }, [items, sortKey]);

  const handleRefresh = () => {
    setRefreshing(true);
    void loadSnapshot(true);
  };

  const handleDelete = async (id: number) => {
    try {
      await csApi.deleteHolding(id);
      await loadSnapshot(true);
    } catch (err) {
      setError(getParsedApiError(err));
    }
  };

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const name = selectedItem?.name || manualName.trim();
    if (!name) return;
    setSaving(true);
    setError(null);
    try {
      await csApi.createHolding({
        item_name: name,
        good_id: selectedItem?.goodId,
        wear: manualWear,
        platform: manualPlatform,
        purchase_price: Number.parseFloat(manualPurchase) || 0,
      });
      setManualName('');
      setManualWear('');
      setManualPurchase('');
      setSelectedItem(null);
      setMode('list');
      await loadSnapshot(true);
    } catch (err) {
      setError(getParsedApiError(err));
    } finally {
      setSaving(false);
    }
  };

  const handleImagePick = async (file: File) => {
    setExtracting(true);
    setError(null);
    try {
      const data = await csApi.previewHoldingsImportImage(file) as {
        sessionId?: string;
        drafts?: Array<Record<string, unknown>>;
      };
      setImportSessionId(data.sessionId ?? null);
      setExtracted((data.drafts ?? []).map((row) => draftFromApi(row)));
      setMode('image');
    } catch (err) {
      setError(getParsedApiError(err));
    } finally {
      setExtracting(false);
    }
  };

  const scheduleRematch = useCallback((sessionId: string, drafts: ExtractedItem[]) => {
    if (rematchTimerRef.current) {
      window.clearTimeout(rematchTimerRef.current);
    }
    rematchTimerRef.current = window.setTimeout(() => {
      void (async () => {
        setRematching(true);
        try {
          const data = await csApi.updateHoldingsImportDrafts({
            session_id: sessionId,
            drafts: draftsToApiPayload(drafts),
            rematch: true,
          }) as { drafts?: Array<Record<string, unknown>> };
          setExtracted((data.drafts ?? []).map((row) => draftFromApi(row)));
        } catch (err) {
          setError(getParsedApiError(err));
        } finally {
          setRematching(false);
        }
      })();
    }, 500);
  }, []);

  const updateDraft = (draftId: string, patch: Partial<ExtractedItem>, rematch = false) => {
    setExtracted((prev) => {
      const next = prev.map((row) => (row.draftId === draftId ? { ...row, ...patch } : row));
      if (rematch && importSessionId) {
        scheduleRematch(importSessionId, next);
      }
      return next;
    });
  };

  const handleImportExtracted = async () => {
    if (!importSessionId) return;
    const selected = extracted.filter((row) => row.checked && row.itemName.trim());
    if (selected.length === 0) return;
    setSaving(true);
    try {
      await csApi.updateHoldingsImportDrafts({
        session_id: importSessionId,
        drafts: draftsToApiPayload(extracted),
        rematch: false,
      });
      await csApi.commitHoldingsImport({
        session_id: importSessionId,
        draft_ids: selected.map((row) => row.draftId),
        skip_duplicates: skipDuplicates,
      });
      setExtracted([]);
      setImportSessionId(null);
      setMode('list');
      await loadSnapshot(true);
    } catch (err) {
      setError(getParsedApiError(err));
    } finally {
      setSaving(false);
    }
  };

  const sortButtons = (
    <div className="flex flex-wrap gap-1.5">
      {([
        ['market', '市场价'],
        ['purchase', '购入价'],
        ['pnl', '盈亏'],
      ] as const).map(([key, label]) => (
        <button
          key={key}
          type="button"
          className={cn(
            'ia-chip text-xs',
            sortKey === key && 'ring-2 ring-[hsl(var(--primary))]',
          )}
          onClick={() => setSortKey(key)}
        >
          {label}
        </button>
      ))}
    </div>
  );

  return (
    <div className="ia-v2-root mx-auto flex min-h-0 w-full max-w-6xl flex-1 flex-col gap-4 px-1 pb-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="label-uppercase">Portfolio</p>
          <h1 className="mt-1 text-xl font-semibold text-foreground">饰品持仓</h1>
          <p className="mt-1 max-w-2xl text-sm text-secondary-text">
            记录购入成本并跟踪市场价与盈亏。支持手动录入或上传截图识别；匹配饰品后可刷新 CSQAQ 市价。
            <Link to="/stocks/portfolio" className="ml-2 text-cyan underline-offset-2 hover:underline">
              股票持仓
            </Link>
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" size="sm" onClick={() => setMode('manual')}>
            <Plus className="h-4 w-4" />
            手动添加
          </Button>
          <Button
            variant="secondary"
            size="sm"
            isLoading={extracting}
            loadingText="识别中…"
            onClick={() => fileRef.current?.click()}
          >
            <Camera className="h-4 w-4" />
            图片导入
          </Button>
          <Button variant="primary" size="sm" isLoading={refreshing} loadingText="刷新中…" onClick={handleRefresh}>
            <RefreshCw className="h-4 w-4" />
            刷新市价
          </Button>
          <input
            ref={fileRef}
            type="file"
            accept="image/jpeg,image/png,image/webp,image/gif"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) void handleImagePick(file);
              e.target.value = '';
            }}
          />
        </div>
      </div>

      {error ? <ApiErrorAlert error={error} /> : null}
      <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
        <StatCard
          label="市场价"
          value={formatMoney(summary.totalMarketValue)}
          hint={`${summary.itemCount ?? 0} 件饰品`}
          icon={<Wallet className="h-5 w-5" />}
          tone="primary"
        />
        <StatCard
          label="总盈亏"
          value={
            <span
              className={cn(
                pnlTone(summary.totalPnl) === 'danger' && 'text-danger',
                pnlTone(summary.totalPnl) === 'success' && 'text-success',
              )}
            >
              {formatPnl(summary.totalPnl)}
            </span>
          }
          hint={summary.totalPnl != null ? '相对购入成本' : '需刷新市价后计算'}
          icon={
            (summary.totalPnl ?? 0) >= 0 ? (
              <TrendingUp className="h-5 w-5" />
            ) : (
              <TrendingDown className="h-5 w-5" />
            )
          }
          tone={pnlTone(summary.totalPnl)}
        />
        <StatCard
          label="购入总价"
          value={formatMoney(summary.totalCost)}
          hint={`${summary.rowCount ?? 0} 条持仓记录`}
          icon={<Package className="h-5 w-5" />}
        />
      </div>

      {mode === 'manual' ? (
        <SectionCard title="手动添加饰品" subtitle="Holdings">
          <form className="space-y-4" onSubmit={(e) => void handleManualSubmit(e)}>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <label className="block space-y-2 text-sm">
                <span className="text-secondary-text">饰品名称</span>
                <CsItemSearchInput
                  value={manualName}
                  onChange={setManualName}
                  selectedItem={selectedItem}
                  onSelect={(item) => {
                    setSelectedItem(item);
                    if (item) setManualName(item.name);
                  }}
                  placeholder="名称 / 皮肤，搜索并选择饰品"
                />
              </label>
              <label className="block space-y-2 text-sm">
                <span className="text-secondary-text">磨损</span>
                <select className={FIELD_CLASS} value={manualWear} onChange={(e) => setManualWear(e.target.value)}>
                  <option value="">未指定</option>
                  {WEAR_OPTIONS.map((w) => (
                    <option key={w} value={w}>{w}</option>
                  ))}
                </select>
              </label>
              <label className="block space-y-2 text-sm">
                <span className="text-secondary-text">购入价</span>
                <input
                  className={FIELD_CLASS}
                  type="number"
                  min="0"
                  step="0.01"
                  value={manualPurchase}
                  onChange={(e) => setManualPurchase(e.target.value)}
                  placeholder="例如 146800"
                />
              </label>
              <label className="block space-y-2 text-sm">
                <span className="text-secondary-text">价格平台</span>
                <select className={FIELD_CLASS} value={manualPlatform} onChange={(e) => setManualPlatform(e.target.value)}>
                  <option value="yyyp">悠悠有品</option>
                  <option value="buff">BUFF</option>
                  <option value="steam">Steam</option>
                </select>
              </label>
            </div>
            <div className="flex justify-end gap-2">
              <Button type="button" variant="ghost" size="sm" onClick={() => setMode('list')}>
                取消
              </Button>
              <Button type="submit" variant="primary" size="sm" isLoading={saving} loadingText="保存中…">
                保存
              </Button>
            </div>
          </form>
        </SectionCard>
      ) : null}

      {mode === 'image' ? (
        <SectionCard
          title="图片识别结果"
          subtitle="Import"
          actions={
            extracted.length > 0 ? (
              <Badge variant="default">{extracted.filter((r) => r.checked).length} 项已选</Badge>
            ) : null
          }
        >
          <p className="mb-4 text-sm text-secondary-text">
            上传第三方库存 App 截图后，系统会匹配饰品并标记低置信度/重复项；确认后再导入。
          </p>
          {extracted.length === 0 ? (
            <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-border/70 bg-card/40 px-6 py-10 text-secondary-text">
              <Upload className="h-8 w-8 opacity-60" />
              <p className="text-sm">点击上方「图片导入」上传截图</p>
            </div>
          ) : (
            <div className="max-h-[28rem] space-y-2 overflow-y-auto">
              {extracted.map((row) => (
                <div
                  key={row.draftId}
                  className={cn(
                    'rounded-xl border bg-card/50 p-3 transition-colors',
                    row.matchConfidence === 'low' || !row.goodId
                      ? 'border-warning/50'
                      : 'border-border/60',
                  )}
                >
                  <div className="flex gap-3">
                    <input
                      type="checkbox"
                      className="mt-2"
                      checked={row.checked}
                      onChange={(e) => updateDraft(row.draftId, { checked: e.target.checked })}
                    />
                    <div className="min-w-0 flex-1 space-y-2">
                      <div className="flex flex-wrap items-center gap-2">
                        {(row.matchConfidence === 'low' || !row.goodId) ? (
                          <Badge variant="warning">待确认</Badge>
                        ) : null}
                        {row.duplicateOf ? <Badge variant="default">已存在 #{row.duplicateOf}</Badge> : null}
                        {row.matchTier ? <Badge variant="default">{row.matchTier}</Badge> : null}
                      </div>
                      <input
                        className={cn(FIELD_CLASS, 'h-9')}
                        value={row.itemName}
                        onChange={(e) => updateDraft(row.draftId, { itemName: e.target.value }, true)}
                        placeholder="饰品名称"
                      />
                      <div className="grid gap-2 sm:grid-cols-3">
                        <select
                          className={cn(FIELD_CLASS, 'h-9')}
                          value={row.wear ?? ''}
                          onChange={(e) => updateDraft(row.draftId, { wear: e.target.value }, true)}
                        >
                          <option value="">磨损</option>
                          {WEAR_OPTIONS.map((wear) => (
                            <option key={wear} value={wear}>{wear}</option>
                          ))}
                        </select>
                        <input
                          className={cn(FIELD_CLASS, 'h-9')}
                          type="number"
                          step="0.0001"
                          min="0"
                          max="1"
                          value={row.floatValue ?? ''}
                          onChange={(e) => updateDraft(
                            row.draftId,
                            { floatValue: e.target.value ? Number.parseFloat(e.target.value) : null },
                            true,
                          )}
                          placeholder="Float"
                        />
                        <input
                          className={cn(FIELD_CLASS, 'h-9')}
                          type="number"
                          step="0.01"
                          min="0"
                          value={row.purchasePrice ?? ''}
                          onChange={(e) => updateDraft(
                            row.draftId,
                            { purchasePrice: e.target.value ? Number.parseFloat(e.target.value) : 0 },
                          )}
                          placeholder="购入价"
                        />
                      </div>
                      <p className="text-xs text-secondary-text">
                        市场价 {formatMoney(row.marketPrice)}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
          {extracted.length > 0 ? (
            <label className="mt-3 flex items-center gap-2 text-sm text-secondary-text">
              <input
                type="checkbox"
                checked={skipDuplicates}
                onChange={(e) => setSkipDuplicates(e.target.checked)}
              />
              跳过与现有持仓重复的条目
            </label>
          ) : null}
          <div className="mt-4 flex justify-end gap-2">
            <Button type="button" variant="ghost" size="sm" onClick={() => { setExtracted([]); setImportSessionId(null); setMode('list'); }}>
              取消
            </Button>
            <Button
              type="button"
              variant="primary"
              size="sm"
              isLoading={saving || rematching}
              loadingText={rematching ? '匹配中…' : '导入中…'}
              disabled={extracted.filter((r) => r.checked).length === 0}
              onClick={() => void handleImportExtracted()}
            >
              导入选中 ({extracted.filter((r) => r.checked).length})
            </Button>
          </div>
        </SectionCard>
      ) : null}

      <SectionCard title="持仓明细" subtitle="Items" actions={sortButtons}>
        {loading ? (
          <EmptyState title="加载中" description="正在读取持仓数据…" className="border-none bg-transparent px-4 py-8 shadow-none" />
        ) : sortedItems.length === 0 ? (
          <EmptyState
            title="暂无持仓"
            description="点击「手动添加」录入饰品，或使用「图片导入」从截图批量识别。"
            className="border-none bg-transparent px-4 py-8 shadow-none"
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b border-border/60 text-xs text-secondary-text">
                <tr>
                  <th className="py-2 pr-3 text-left">饰品</th>
                  <th className="py-2 pr-3 text-right">市场价</th>
                  <th className="py-2 pr-3 text-right">购入价</th>
                  <th className="py-2 pr-3 text-right">盈亏</th>
                  <th className="py-2 text-right">操作</th>
                </tr>
              </thead>
              <tbody>
                {sortedItems.map((row) => {
                  const wearLabel = displayHoldingsWear(row.itemName, row.wear);
                  return (
                  <tr key={row.id} className="border-b border-border/40">
                    <td className="py-3 pr-3">
                      <div className="flex items-center gap-3">
                        {row.thumbnailUrl ? (
                          <img
                            src={row.thumbnailUrl}
                            alt=""
                            className="h-11 w-11 shrink-0 rounded-lg border border-border/50 object-cover bg-card"
                          />
                        ) : (
                          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg border border-border/50 bg-card/60 text-secondary-text">
                            <Package className="h-4 w-4" />
                          </div>
                        )}
                        <div className="min-w-0">
                          <div className="truncate font-medium text-foreground">
                            {displayHoldingsTitle(row.itemName, row.wear)}
                          </div>
                          <div className="mt-0.5 flex flex-wrap gap-1.5">
                            {wearLabel ? (
                              <span className="text-xs text-secondary-text">{wearLabel}</span>
                            ) : null}
                            {row.itemName ? (
                              <Link
                                to={`/chat?name=${encodeURIComponent(row.itemName)}&platform=${encodeURIComponent(row.platform ?? 'yyyp')}`}
                                className="text-xs text-cyan hover:underline"
                              >
                                问饰品
                              </Link>
                            ) : null}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 pr-3 text-right tabular-nums">{formatMoney(row.marketPrice)}</td>
                    <td className="py-3 pr-3 text-right tabular-nums">{formatMoney(row.purchasePrice)}</td>
                    <td
                      className={cn(
                        'py-3 pr-3 text-right tabular-nums',
                        pnlTone(row.pnl) === 'success' && 'text-success',
                        pnlTone(row.pnl) === 'danger' && 'text-danger',
                        pnlTone(row.pnl) === 'default' && 'text-secondary-text',
                      )}
                    >
                      {formatPnl(row.pnl)}
                    </td>
                    <td className="py-3 text-right">
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        aria-label={`删除 ${row.itemName}`}
                        onClick={() => void handleDelete(row.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </td>
                  </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </SectionCard>
    </div>
  );
};

export default CsHoldingsPage;
