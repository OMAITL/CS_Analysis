import apiClient from './index';
import { normalizeCsAnalyzeResponse } from './csNormalize';
import { CS_ITEM_ANALYZE_TIMEOUT_MS } from '../utils/constants';
import { toCamelCase } from './utils';
import type { CsItemAnalyzeRequest, CsItemAnalyzeResponse, CsItemSearchRequest, CsItemSearchResponse } from '../types/cs';
import type { CsSkillInfo } from '../types/csHome';

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
};
