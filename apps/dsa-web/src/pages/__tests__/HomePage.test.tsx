import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { csApi } from '../../api/cs';
import HomePage from '../HomePage';

vi.mock('../../api/cs', () => ({
  csApi: {
    analyze: vi.fn(),
    listSkills: vi.fn(),
    searchItems: vi.fn(),
  },
}));

const mockAnalyzeResponse = {
  goodId: 769,
  itemName: '法玛斯 | 机械工业 (崭新出厂)',
  marketHashName: 'FAMAS | Mecha Industries (Factory New)',
  platform: 'yyyp',
  snapshot: { yyypSellPrice: 12.5 },
  meta: {
    goodId: 769,
    itemName: '法玛斯 | 机械工业 (崭新出厂)',
    marketHashName: 'FAMAS | Mecha Industries (Factory New)',
    platform: 'yyyp',
    ohlcSource: 'mixed',
    volumeSource: 'kline_chart_all_v',
    dataQuality: 'full',
    rowCount: 30,
    crawlRows: 20,
    apiRows: 30,
    periodDays: 365,
  },
  trend: {
    code: 'FAMAS',
    trendStatus: '弱势多头',
    maAlignment: '多头排列',
    currentPrice: 12.5,
    ma5: 12.1,
    ma10: 11.9,
    ma20: 11.5,
    ma60: 11.0,
    biasMa5: 3.2,
    volumeStatus: '放量',
    volumeRatio5d: 1.2,
    buySignal: '观望',
    signalScore: 62,
    signalReasons: ['MA5 上穿 MA10'],
    riskFactors: ['乖离偏大'],
    macdStatus: '金叉',
    rsiStatus: '中性',
    macdDif: 0.1,
    macdDea: 0.05,
    rsi12: 55,
  },
  ohlcv: [
    { date: '2026-06-01', open: 12, high: 12.6, low: 11.9, close: 12.5, volume: 10, changePercent: 1.2 },
  ],
  reportMarkdown: '## 核心结论\n\n测试结论',
  reportSource: 'template' as const,
  eventIntel: [],
};

describe('HomePage (CS)', () => {
  beforeEach(() => {
    vi.mocked(csApi.listSkills).mockResolvedValue({ skills: [], default: ['bull_trend'] });
    vi.mocked(csApi.searchItems).mockResolvedValue({
      items: [
        {
          goodId: 769,
          name: '法玛斯 | 机械工业 (崭新出厂)',
          marketHashName: 'FAMAS | Mecha Industries (Factory New)',
        },
      ],
      pageIndex: 1,
      pageSize: 20,
      total: 1,
    });
    vi.mocked(csApi.analyze).mockResolvedValue(mockAnalyzeResponse);
    localStorage.clear();
  });

  it('renders CS agent workbench empty state', async () => {
    render(
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>,
    );

    expect(await screen.findByTestId('home-dashboard')).toBeInTheDocument();
    expect(screen.getByText('分析报告将显示在这里')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /启动 Agent 分析/ })).toBeDisabled();
  });

  it('submits analyze via preset task and shows result overview', async () => {
    render(
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole('button', { name: /蝴蝶刀 北方森林/ }));

    await waitFor(() => {
      expect(csApi.analyze).toHaveBeenCalled();
    });

    expect(await screen.findByText('AI 评分')).toBeInTheDocument();
    expect(screen.getByText('分析报告')).toBeInTheDocument();
  });
});
