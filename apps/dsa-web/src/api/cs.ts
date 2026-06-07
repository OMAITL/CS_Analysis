import apiClient from './index';
import { normalizeCsAnalyzeResponse } from './csNormalize';
import { CS_ITEM_ANALYZE_TIMEOUT_MS, API_BASE_URL } from '../utils/constants';
import { toCamelCase } from './utils';
import { createApiError, isApiRequestError, parseApiError } from './error';
import type { CsItemAnalyzeRequest, CsItemAnalyzeResponse, CsItemSearchRequest, CsItemSearchResponse } from '../types/cs';
import type { CsSkillInfo } from '../types/csHome';

export interface CsChatStreamRequest {
  message: string;
  session_id?: string;
  skills?: string[];
  context?: {
    scope?: 'market' | 'portfolio' | 'single_item' | 'general';
    good_id?: number;
    item_name?: string;
    platform?: string;
    previous_analysis_summary?: string;
  };
}

export interface CsChatSessionItem {
  session_id: string;
  title: string;
  message_count: number;
  created_at: string | null;
  last_active: string | null;
}

export interface CsChatSessionMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string | null;
}

export interface CsChatStreamOptions {
  signal?: AbortSignal;
}

export const csApi = {
  searchItems: async (params: CsItemSearchRequest): Promise<CsItemSearchResponse> => {
    const response = await apiClient.get<Record<string, unknown>>('/api/v1/cs/items/search', {
      params: {
        search: params.search,
        page_index: params.pageIndex ?? 1,
        page_size: params.pageSize ?? 20,
      },
    });
    const data = toCamelCase<CsItemSearchResponse>(response.data);
    return {
      items: (data.items ?? []).map((row) => ({
        goodId: row.goodId ?? 0,
        name: row.name ?? '',
        marketHashName: row.marketHashName ?? '',
      })),
      pageIndex: data.pageIndex ?? 1,
      pageSize: data.pageSize ?? 20,
      total: data.total ?? 0,
    };
  },

  analyze: async (params: CsItemAnalyzeRequest): Promise<CsItemAnalyzeResponse> => {
    const body: Record<string, unknown> = {};
    if (params.goodId != null) body.good_id = params.goodId;
    if (params.item) body.item = params.item;
    if (params.platform) body.platform = params.platform;
    if (params.period != null) body.period = params.period;
    if (params.preferCrawl != null) body.prefer_crawl = params.preferCrawl;
    if (params.refreshCrawl != null) body.refresh_crawl = params.refreshCrawl;
    if (params.refreshToday != null) body.refresh_today = params.refreshToday;
    if (params.klinePages != null) body.kline_pages = params.klinePages;
    if (params.includeReport != null) body.include_report = params.includeReport;
    if (params.skills?.length) body.skills = params.skills;

    const response = await apiClient.post<Record<string, unknown>>(
      '/api/v1/cs/items/analyze',
      body,
      { timeout: CS_ITEM_ANALYZE_TIMEOUT_MS },
    );
    return normalizeCsAnalyzeResponse(toCamelCase<CsItemAnalyzeResponse>(response.data));
  },

  listSkills: async (): Promise<{ skills: CsSkillInfo[]; default: string[] }> => {
    const response = await apiClient.get<Record<string, unknown>>('/api/v1/cs/items/skills');
    const data = toCamelCase<{ skills: Array<Record<string, string>>; default: string[] }>(response.data);
    const skills: CsSkillInfo[] = (data.skills ?? []).map((row) => ({
      id: row.id ?? '',
      displayName: row.displayName ?? row.id ?? '',
      description: row.description ?? '',
      category: row.category ?? '',
      source: row.source ?? '',
    }));
    return { skills, default: data.default ?? [] };
  },

  getChatSessions: async (limit = 50): Promise<CsChatSessionItem[]> => {
    const response = await apiClient.get<{ sessions: CsChatSessionItem[] }>('/api/v1/cs/chat/sessions', {
      params: { limit },
    });
    return response.data.sessions ?? [];
  },

  getChatSessionMessages: async (sessionId: string): Promise<CsChatSessionMessage[]> => {
    const response = await apiClient.get<{ messages: CsChatSessionMessage[] }>(
      `/api/v1/cs/chat/sessions/${encodeURIComponent(sessionId)}`,
    );
    return (response.data.messages ?? []).map((row, index) => ({
      id: String(row.id ?? index),
      role: row.role === 'assistant' ? 'assistant' : 'user',
      content: row.content ?? '',
      created_at: row.created_at ?? null,
    }));
  },

  deleteChatSession: async (sessionId: string): Promise<void> => {
    await apiClient.delete(`/api/v1/cs/chat/sessions/${encodeURIComponent(sessionId)}`);
  },

  chatStream: async (
    payload: CsChatStreamRequest,
    options?: CsChatStreamOptions,
  ): Promise<Response> => {
    const base = API_BASE_URL || '';
    const url = `${base}/api/v1/cs/chat/stream`;
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: payload.message,
          session_id: payload.session_id,
          skills: payload.skills,
          context: payload.context,
        }),
        credentials: 'include',
        signal: options?.signal,
      });

      if (response.ok) {
        return response;
      }

      const contentType = response.headers.get('content-type') || '';
      let responseData: unknown = null;
      if (contentType.includes('application/json')) {
        responseData = await response.json().catch(() => null);
      } else {
        responseData = await response.text().catch(() => null);
      }

      const parsed = parseApiError({
        response: {
          status: response.status,
          statusText: response.statusText,
          data: responseData,
        },
      });
      throw createApiError(parsed, {
        response: {
          status: response.status,
          statusText: response.statusText,
          data: responseData,
        },
      });
    } catch (error: unknown) {
      if (isApiRequestError(error)) {
        throw error;
      }
      if (error instanceof Error && error.name === 'AbortError') {
        throw error;
      }
      const parsed = parseApiError(error);
      throw createApiError(parsed, { cause: error });
    }
  },

  getHoldingsSnapshot: async (refreshPrices = true) => {
    const response = await apiClient.get<Record<string, unknown>>('/api/v1/cs/holdings/snapshot', {
      params: { refresh_prices: refreshPrices },
    });
    return toCamelCase(response.data);
  },

  getHoldingsRisk: async (refreshPrices = true, platform?: string) => {
    const response = await apiClient.get<Record<string, unknown>>('/api/v1/cs/holdings/risk', {
      params: {
        refresh_prices: refreshPrices,
        ...(platform ? { platform } : {}),
      },
    });
    return toCamelCase(response.data);
  },

  rematchHoldingsGoodIds: async () => {
    const response = await apiClient.post<Record<string, unknown>>('/api/v1/cs/holdings/rematch-good-ids');
    return toCamelCase(response.data);
  },

  createHolding: async (body: Record<string, unknown>) => {
    const response = await apiClient.post<Record<string, unknown>>('/api/v1/cs/holdings', body);
    return toCamelCase(response.data);
  },

  bulkCreateHoldings: async (items: Record<string, unknown>[]) => {
    const response = await apiClient.post<Record<string, unknown>>('/api/v1/cs/holdings/bulk', { items });
    return toCamelCase(response.data);
  },

  updateHolding: async (id: number, body: Record<string, unknown>) => {
    const response = await apiClient.put<Record<string, unknown>>(`/api/v1/cs/holdings/${id}`, body);
    return toCamelCase(response.data);
  },

  deleteHolding: async (id: number) => {
    await apiClient.delete(`/api/v1/cs/holdings/${id}`);
  },

  extractHoldingsFromImage: async (file: File) => {
    const form = new FormData();
    form.append('file', file);
    const response = await apiClient.post<Record<string, unknown>>(
      '/api/v1/cs/holdings/extract-from-image',
      form,
      { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 150000 },
    );
    return toCamelCase(response.data);
  },

  previewHoldingsImport: async (body: Record<string, unknown>) => {
    const response = await apiClient.post<Record<string, unknown>>('/api/v1/cs/holdings/import/preview', body);
    return toCamelCase(response.data);
  },

  previewHoldingsImportImage: async (file: File) => {
    const form = new FormData();
    form.append('file', file);
    const response = await apiClient.post<Record<string, unknown>>(
      '/api/v1/cs/holdings/import/preview/image',
      form,
      { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 150000 },
    );
    return toCamelCase(response.data);
  },

  updateHoldingsImportDrafts: async (body: Record<string, unknown>) => {
    const response = await apiClient.post<Record<string, unknown>>('/api/v1/cs/holdings/import/update', body);
    return toCamelCase(response.data);
  },

  commitHoldingsImport: async (body: Record<string, unknown>) => {
    const response = await apiClient.post<Record<string, unknown>>('/api/v1/cs/holdings/import/commit', body);
    return toCamelCase(response.data);
  },
};
