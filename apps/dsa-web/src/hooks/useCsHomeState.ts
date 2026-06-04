import { useCallback, useEffect, useMemo, useState } from 'react';
import { csApi } from '../api/cs';
import { getParsedApiError, type ParsedApiError } from '../api/error';
import type { CsHomeHistoryItem } from '../types/csHome';
import type { CsGoodIdItem } from '../types/cs';

const STORAGE_KEY = 'dsa_cs_home_history_v1';
const MAX_HISTORY = 30;

function loadHistory(): CsHomeHistoryItem[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return [];
    }
    const parsed = JSON.parse(raw) as CsHomeHistoryItem[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function saveHistory(items: CsHomeHistoryItem[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items.slice(0, MAX_HISTORY)));
  } catch {
    // ignore quota errors
  }
}

function parseSearchQuery(query: string): { goodId?: number; item?: string } {
  const trimmed = query.trim();
  if (!trimmed) {
    return {};
  }
  if (/^\d+$/.test(trimmed)) {
    return { goodId: Number.parseInt(trimmed, 10) };
  }
  return { item: trimmed };
}

function buildHistoryEntry(result: CsItemAnalyzeResponse): CsHomeHistoryItem {
  return {
    id: `${result.goodId}-${Date.now()}`,
    goodId: result.goodId,
    itemName: result.itemName,
    marketHashName: result.marketHashName,
    platform: result.platform,
    signalScore: result.trend.signalScore,
    buySignal: result.trend.buySignal,
    createdAt: new Date().toISOString(),
    result,
  };
}

export function useCsHomeState() {
  const [query, setQuery] = useState('769');
  const [selectedItem, setSelectedItem] = useState<CsGoodIdItem | null>(null);
  const [platform, setPlatform] = useState('yyyp');
  const [refreshCrawl, setRefreshCrawl] = useState(false);
  const [selectedSkillId, setSelectedSkillId] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<ParsedApiError | null>(null);
  const [inputError, setInputError] = useState<string | null>(null);
  const [result, setResult] = useState<CsItemAnalyzeResponse | null>(null);
  const [historyItems, setHistoryItems] = useState<CsHomeHistoryItem[]>(() => loadHistory());
  const [selectedHistoryId, setSelectedHistoryId] = useState<string | null>(null);

  useEffect(() => {
    saveHistory(historyItems);
  }, [historyItems]);

  const clearError = useCallback(() => setError(null), []);

  const selectHistoryItem = useCallback((id: string) => {
    const item = historyItems.find((entry) => entry.id === id);
    if (!item) {
      return;
    }
    setSelectedHistoryId(id);
    setResult(item.result);
    setQuery(String(item.goodId));
    setSelectedItem({
      goodId: item.goodId,
      name: item.itemName,
      marketHashName: item.marketHashName,
    });
    setPlatform(item.platform);
    setError(null);
    setInputError(null);
  }, [historyItems]);

  const deleteHistoryItem = useCallback((id: string) => {
    setHistoryItems((prev) => {
      const next = prev.filter((entry) => entry.id !== id);
      if (selectedHistoryId === id) {
        setSelectedHistoryId(null);
        setResult(null);
      }
      return next;
    });
  }, [selectedHistoryId]);

  const clearHistory = useCallback(() => {
    setHistoryItems([]);
    setSelectedHistoryId(null);
    setResult(null);
  }, []);

  const submitAnalysis = useCallback(async (overrideQuery?: string) => {
    const searchText = (overrideQuery ?? query).trim();
    if (!searchText) {
      setInputError('请输入饰品名称或 good_id');
      return;
    }

    let goodId: number | undefined;
    let item: string | undefined;

    if (selectedItem && (!overrideQuery || overrideQuery === query)) {
      goodId = selectedItem.goodId;
    } else {
      const parsed = parseSearchQuery(searchText);
      goodId = parsed.goodId;
      item = parsed.item;
    }

    if (!goodId && item) {
      try {
        const searchResult = await csApi.searchItems({ search: item, pageSize: 20 });
        if (searchResult.total === 0) {
          setInputError('未找到匹配的饰品，请换个关键词');
          return;
        }
        if (searchResult.total > 1) {
          setInputError(
            `「${item}」匹配到 ${searchResult.total} 个饰品，请从下拉列表中选择具体磨损/款式后再分析`,
          );
          return;
        }
        goodId = searchResult.items[0]?.goodId;
        if (goodId) {
          setSelectedItem(searchResult.items[0]);
          setQuery(searchResult.items[0].name);
        }
      } catch (err) {
        setError(getParsedApiError(err));
        return;
      }
    }

    if (!goodId) {
      setInputError('请选择列表中的具体饰品，或直接输入 good_id');
      return;
    }

    setInputError(null);
    setError(null);
    setIsAnalyzing(true);

    try {
      const response = await csApi.analyze({
        goodId,
        platform: platform || 'yyyp',
        preferCrawl: true,
        refreshCrawl,
        includeReport: true,
        skills: selectedSkillId ? [selectedSkillId] : undefined,
      });
      const entry = buildHistoryEntry(response);
      setHistoryItems((prev) => [entry, ...prev.filter((h) => h.goodId !== response.goodId)].slice(0, MAX_HISTORY));
      setSelectedHistoryId(entry.id);
      setResult(response);
      setQuery(response.itemName);
      setSelectedItem({
        goodId: response.goodId,
        name: response.itemName,
        marketHashName: response.marketHashName,
      });
    } catch (err) {
      setError(getParsedApiError(err));
      setResult(null);
    } finally {
      setIsAnalyzing(false);
    }
  }, [platform, query, refreshCrawl, selectedItem, selectedSkillId]);

  const selectedHistoryIds = useMemo(
    () => (selectedHistoryId ? [selectedHistoryId] : []),
    [selectedHistoryId],
  );

  return {
    query,
    platform,
    refreshCrawl,
    selectedSkillId,
    isAnalyzing,
    error,
    inputError,
    result,
    historyItems,
    selectedHistoryId,
    selectedHistoryIds,
    setQuery,
    setSelectedItem,
    selectedItem,
    setPlatform,
    setRefreshCrawl,
    setSelectedSkillId,
    clearError,
    selectHistoryItem,
    deleteHistoryItem,
    clearHistory,
    submitAnalysis,
  };
}

export default useCsHomeState;
