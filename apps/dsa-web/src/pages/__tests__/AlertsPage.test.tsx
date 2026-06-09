import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { csApi } from '../../api/cs';
import AlertsPage from '../AlertsPage';

const {
  listRules,
  createRule,
  deleteRule,
  enableRule,
  disableRule,
  testRule,
  listTriggers,
  listNotifications,
} = vi.hoisted(() => ({
  listRules: vi.fn(),
  createRule: vi.fn(),
  deleteRule: vi.fn(),
  enableRule: vi.fn(),
  disableRule: vi.fn(),
  testRule: vi.fn(),
  listTriggers: vi.fn(),
  listNotifications: vi.fn(),
}));

vi.mock('../../api/alerts', () => ({
  alertsApi: {
    listRules,
    createRule,
    deleteRule,
    enableRule,
    disableRule,
    testRule,
    listTriggers,
    listNotifications,
  },
}));

vi.mock('../../api/cs', () => ({
  csApi: {
    searchItems: vi.fn(),
  },
}));

const csSearchItem = {
  goodId: 769,
  name: 'AK-47 | 二西莫夫',
  marketHashName: 'AK-47 | Asiimov (Field-Tested)',
};

async function selectCsAlertTargetItem() {
  vi.mocked(csApi.searchItems).mockResolvedValue({
    items: [csSearchItem],
    pageIndex: 1,
    pageSize: 20,
    total: 1,
  });
  fireEvent.change(screen.getByLabelText('目标饰品'), { target: { value: 'AK' } });
  await waitFor(() => expect(csApi.searchItems).toHaveBeenCalled());
  const listbox = await screen.findByRole('listbox');
  fireEvent.click(within(listbox).getByText('AK-47 | 二西莫夫'));
}

const parsedError = {
  title: '加载失败',
  message: '告警 API 不可用',
  rawMessage: '告警 API 不可用',
  category: 'http_error' as const,
  status: 500,
};

const rule = {
  id: 1,
  name: 'CS 自动止盈 · AK-47 | 二西莫夫 ≥ 120',
  targetScope: 'cs_item' as const,
  target: '769',
  alertType: 'cs_price_cross' as const,
  parameters: { direction: 'above' as const, price: 120, platform: 'yyyp' as const },
  severity: 'warning' as const,
  enabled: true,
  source: 'cs_auto',
  createdAt: '2026-05-18T09:00:00',
  updatedAt: '2026-05-18T09:30:00',
};

function createDeferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((promiseResolve) => {
    resolve = promiseResolve;
  });
  return { promise, resolve };
}

beforeEach(() => {
  vi.clearAllMocks();
  listRules.mockResolvedValue({ items: [rule], total: 1, page: 1, pageSize: 20 });
  listTriggers.mockResolvedValue({
    items: [
      {
        id: 10,
        ruleId: 1,
        target: 'cs_item:769',
        observedValue: 125,
        threshold: 120,
        reason: 'CS item 769 price above 120.00',
        dataSource: 'csqaq',
        dataTimestamp: '2026-05-18T09:30:00',
        triggeredAt: '2026-05-18T09:30:01',
        status: 'triggered',
      },
    ],
    total: 1,
    page: 1,
    pageSize: 20,
  });
  listNotifications.mockResolvedValue({ items: [], total: 0, page: 1, pageSize: 20 });
  testRule.mockResolvedValue({
    ruleId: 1,
    status: 'triggered',
    triggered: true,
    observedValue: 125,
    message: 'CS item 769 price above 120.00',
  });
  createRule.mockResolvedValue(rule);
  disableRule.mockResolvedValue({ ...rule, enabled: false });
  enableRule.mockResolvedValue(rule);
  deleteRule.mockResolvedValue({ deleted: 1 });
});

describe('AlertsPage', () => {
  it('loads CS rules, trigger history, and notification empty state', async () => {
    render(<AlertsPage />);

    expect(screen.getByText(/管理 CS 饰品持仓的价格提醒与风险监控/)).toBeInTheDocument();
    expect(await screen.findByText('CS 自动止盈 · AK-47 | 二西莫夫 ≥ 120')).toBeInTheDocument();
    expect(await screen.findByText('CS item 769 price above 120.00')).toBeInTheDocument();
    expect(await screen.findByText('暂无通知尝试记录')).toBeInTheDocument();
    expect(listRules).toHaveBeenCalledWith({
      enabled: undefined,
      alertType: undefined,
      csOnly: true,
      page: 1,
      pageSize: 20,
    });
    expect(listTriggers).toHaveBeenCalledWith({ page: 1, pageSize: 20, csOnly: true });
    expect(listNotifications).toHaveBeenCalledWith({ page: 1, pageSize: 20 });
  });

  it('runs a dry-run test and renders only declared response fields', async () => {
    listTriggers.mockResolvedValueOnce({ items: [], total: 0, page: 1, pageSize: 20 });
    render(<AlertsPage />);

    fireEvent.click(await screen.findByRole('button', { name: '测试' }));

    await waitFor(() => expect(testRule).toHaveBeenCalledWith(1));
    expect(await screen.findByText('测试结果')).toBeInTheDocument();
    expect(screen.getByText(/CS item 769 price above 120.00/)).toBeInTheDocument();
    expect(screen.getByText(/观察值：125/)).toBeInTheDocument();
    expect(screen.queryByText(/csqaq/)).not.toBeInTheDocument();
  });

  it('renders batch dry-run summary and target results', async () => {
    testRule.mockResolvedValueOnce({
      ruleId: 1,
      targetScope: 'cs_holdings',
      status: 'triggered',
      triggered: true,
      observedValue: 11,
      message: 'Evaluated 2 targets',
      evaluatedCount: 2,
      triggeredCount: 1,
      degradedCount: 1,
      skippedCount: 0,
      targetResults: [
        {
          target: '769',
          displayTarget: '饰品 769',
          status: 'triggered',
          recordStatus: 'triggered',
          triggered: true,
          observedValue: 11,
          message: 'triggered',
        },
        {
          target: '770',
          displayTarget: '饰品 770',
          status: 'not_triggered',
          recordStatus: 'degraded',
          triggered: false,
          observedValue: null,
          message: 'degraded',
        },
      ],
    });
    render(<AlertsPage />);

    fireEvent.click(await screen.findByRole('button', { name: '测试' }));

    expect(await screen.findByText(/评估 2 · 触发 1 · 降级 1 · 跳过 0/)).toBeInTheDocument();
    expect(screen.getByText('饰品 769')).toBeInTheDocument();
    expect(screen.getByText(/not_triggered \/ degraded/)).toBeInTheDocument();
  });

  it('creates a CS rule through the page form and reloads rules', async () => {
    render(<AlertsPage />);

    await screen.findByText('CS 自动止盈 · AK-47 | 二西莫夫 ≥ 120');
    fireEvent.change(screen.getByLabelText('目标范围'), { target: { value: 'cs_item' } });
    await selectCsAlertTargetItem();
    fireEvent.change(screen.getByLabelText('价格阈值'), { target: { value: '200' } });
    fireEvent.click(screen.getByRole('button', { name: '创建规则' }));

    await waitFor(() => {
      expect(createRule).toHaveBeenCalledWith(expect.objectContaining({
        targetScope: 'cs_item',
        target: '769',
        alertType: 'cs_price_cross',
        parameters: { direction: 'above', price: 200, platform: 'yyyp' },
      }));
    });
    expect(await screen.findByText(/已创建告警规则/)).toBeInTheDocument();
  });

  it('keeps create form values when create API fails', async () => {
    createRule.mockRejectedValueOnce({ parsedError });
    render(<AlertsPage />);

    await screen.findByText('CS 自动止盈 · AK-47 | 二西莫夫 ≥ 120');
    fireEvent.change(screen.getByLabelText('目标范围'), { target: { value: 'cs_item' } });
    await selectCsAlertTargetItem();
    fireEvent.change(screen.getByLabelText('价格阈值'), { target: { value: '200' } });
    fireEvent.click(screen.getByRole('button', { name: '创建规则' }));

    expect(await screen.findByText('加载失败')).toBeInTheDocument();
    expect(screen.getByLabelText('目标饰品')).toHaveValue('AK-47 | 二西莫夫');
    expect(screen.getByLabelText('价格阈值')).toHaveValue(200);
  });

  it('clamps rules pagination when a mutation leaves the current page empty', async () => {
    const page2Rule = { ...rule, id: 2, name: '第二页 CS 规则', target: '770' };
    listRules
      .mockResolvedValueOnce({ items: [rule], total: 21, page: 1, pageSize: 20 })
      .mockResolvedValueOnce({ items: [page2Rule], total: 21, page: 2, pageSize: 20 })
      .mockResolvedValueOnce({ items: [], total: 20, page: 2, pageSize: 20 })
      .mockResolvedValue({ items: [rule], total: 20, page: 1, pageSize: 20 });

    render(<AlertsPage />);

    expect(await screen.findByText('CS 自动止盈 · AK-47 | 二西莫夫 ≥ 120')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '2' }));
    expect(await screen.findByText('第二页 CS 规则')).toBeInTheDocument();
    fireEvent.click(screen.getByLabelText('删除 第二页 CS 规则'));
    fireEvent.click(await screen.findByRole('button', { name: '删除' }));

    await waitFor(() => expect(deleteRule).toHaveBeenCalledWith(2));
    await waitFor(() => {
      expect(listRules).toHaveBeenCalledWith({
        enabled: undefined,
        alertType: undefined,
        csOnly: true,
        page: 1,
        pageSize: 20,
      });
    });
    expect(await screen.findByText('CS 自动止盈 · AK-47 | 二西莫夫 ≥ 120')).toBeInTheDocument();
  });

  it('keeps the latest rules response when filter requests resolve out of order', async () => {
    const initialRequest = createDeferred<{ items: Array<typeof rule>; total: number; page: number; pageSize: number }>();
    const filteredRequest = createDeferred<{ items: Array<typeof rule>; total: number; page: number; pageSize: number }>();
    const staleRule = { ...rule, id: 3, name: '旧筛选规则', enabled: true };
    const filteredRule = { ...rule, id: 4, name: '停用规则', enabled: false };
    listRules
      .mockReset()
      .mockReturnValueOnce(initialRequest.promise)
      .mockReturnValueOnce(filteredRequest.promise);

    render(<AlertsPage />);

    fireEvent.change(screen.getByLabelText('启停状态'), { target: { value: 'disabled' } });
    await waitFor(() => expect(listRules).toHaveBeenCalledTimes(2));

    filteredRequest.resolve({ items: [filteredRule], total: 1, page: 1, pageSize: 20 });
    expect(await screen.findByText('停用规则')).toBeInTheDocument();

    initialRequest.resolve({ items: [staleRule], total: 1, page: 1, pageSize: 20 });
    await waitFor(() => expect(screen.queryByText('旧筛选规则')).not.toBeInTheDocument());
    expect(screen.getByText('停用规则')).toBeInTheDocument();
  });

  it('renders API errors through ApiErrorAlert', async () => {
    listRules.mockRejectedValueOnce({ parsedError });

    render(<AlertsPage />);

    expect(await screen.findByText('加载失败')).toBeInTheDocument();
    expect(screen.getByText('告警 API 不可用')).toBeInTheDocument();
  });
});
