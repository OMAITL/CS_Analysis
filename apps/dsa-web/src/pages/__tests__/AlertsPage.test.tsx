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
    getHoldingsSnapshot: vi.fn(),
  },
}));

const csSearchItem = {
  goodId: 769,
  name: 'AK-47 | 二西莫夫',
  marketHashName: 'AK-47 | Asiimov (Field-Tested)',
};

async function openCreateDrawer() {
  fireEvent.click(screen.getByRole('button', { name: '新建规则' }));
  await screen.findByRole('dialog', { name: '新建告警规则' });
}

async function selectCsAlertTargetItem() {
  vi.mocked(csApi.searchItems).mockResolvedValue({
    items: [csSearchItem],
    pageIndex: 1,
    pageSize: 5,
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
  listRules.mockResolvedValue({ items: [rule], total: 1, page: 1, pageSize: 5 });
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
    pageSize: 5,
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
  vi.mocked(csApi.getHoldingsSnapshot).mockResolvedValue({ items: [] });
});

describe('AlertsPage', () => {
  it('loads monitor dashboard and rules', async () => {
    render(<AlertsPage />);

    expect(await screen.findByLabelText('今日监控概览')).toBeInTheDocument();
    expect(within(await screen.findByRole('table')).getByText('AK-47 | 二西莫夫')).toBeInTheDocument();
    expect(screen.queryByText('今日动态')).not.toBeInTheDocument();
    expect(screen.queryByText('触发历史')).not.toBeInTheDocument();
    expect(screen.queryByText('快捷模板')).not.toBeInTheDocument();
    expect(listRules).toHaveBeenCalledWith(expect.objectContaining({
      csOnly: true,
      page: 1,
      pageSize: 100,
    }));
    expect(listRules).toHaveBeenCalledWith(expect.objectContaining({
      csOnly: true,
      enabled: true,
      pageSize: 100,
    }));
    expect(listTriggers).toHaveBeenCalledWith({ page: 1, pageSize: 5, csOnly: true });
    expect(csApi.getHoldingsSnapshot).toHaveBeenCalledWith(false);
  });

  it('runs a dry-run test and renders only declared response fields', async () => {
    listTriggers.mockResolvedValueOnce({ items: [], total: 0, page: 1, pageSize: 20 });
    render(<AlertsPage />);

    fireEvent.click(await screen.findByRole('button', { name: '测试' }));

    await waitFor(() => expect(testRule).toHaveBeenCalledWith(1));
    expect(await screen.findByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('测试结果')).toBeInTheDocument();
    expect(screen.getByText(/CS item 769 price above 120.00/)).toBeInTheDocument();
  });

  it('renders dry-run message from API response', async () => {
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
    });
    render(<AlertsPage />);

    fireEvent.click(await screen.findByRole('button', { name: '测试' }));

    expect(await screen.findByText('Evaluated 2 targets')).toBeInTheDocument();
  });

  it('creates a CS rule through the page form and reloads rules', async () => {
    render(<AlertsPage />);

    await within(await screen.findByRole('table')).findByText('AK-47 | 二西莫夫');
    await openCreateDrawer();
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

    await within(await screen.findByRole('table')).findByText('AK-47 | 二西莫夫');
    await openCreateDrawer();
    fireEvent.change(screen.getByLabelText('目标范围'), { target: { value: 'cs_item' } });
    await selectCsAlertTargetItem();
    fireEvent.change(screen.getByLabelText('价格阈值'), { target: { value: '200' } });
    fireEvent.click(screen.getByRole('button', { name: '创建规则' }));

    expect(await screen.findByText('加载失败')).toBeInTheDocument();
    expect(screen.getByLabelText('目标饰品')).toHaveValue('AK-47 | 二西莫夫');
    expect(screen.getByLabelText('价格阈值')).toHaveValue(200);
  });

  it('clamps rules pagination when a mutation leaves the current page empty', async () => {
    const page2Rule = {
      ...rule,
      id: 2,
      name: 'CS 自动止盈 · 第二页饰品 ≥ 120',
      target: '770',
    };
    let page2Deleted = false;
    const fillerRules = Array.from({ length: 4 }, (_, index) => ({
      ...rule,
      id: index + 3,
      name: `CS 自动止盈 · 填充饰品 ${index} ≥ 120`,
      target: String(800 + index),
    }));
    const allRules = [rule, ...fillerRules, page2Rule];

    deleteRule.mockImplementation(async (ruleId: number) => {
      if (ruleId === 2) {
        page2Deleted = true;
      }
      return { deleted: 1 };
    });
    listRules.mockImplementation(() => {
      const items = page2Deleted ? allRules.filter((item) => item.id !== 2) : allRules;
      return Promise.resolve({
        items,
        total: items.length,
        page: 1,
        pageSize: 100,
      });
    });

    render(<AlertsPage />);

    const table = await screen.findByRole('table');
    expect(within(table).getByText('AK-47 | 二西莫夫')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '2' }));
    await waitFor(() => expect(within(screen.getByRole('table')).getByText('第二页饰品')).toBeInTheDocument());
    fireEvent.click(screen.getByLabelText('删除 CS 自动止盈 · 第二页饰品 ≥ 120'));
    fireEvent.click(await screen.findByRole('button', { name: '删除' }));

    await waitFor(() => expect(deleteRule).toHaveBeenCalledWith(2));
    await waitFor(() => {
      expect(listRules).toHaveBeenCalledWith(expect.objectContaining({
        csOnly: true,
        page: 1,
        pageSize: 100,
      }));
    });
    await waitFor(() => {
      expect(within(screen.getByRole('table')).getByText('AK-47 | 二西莫夫')).toBeInTheDocument();
    });
  });

  it('keeps the latest rules response when filter requests resolve out of order', async () => {
    const initialRequest = createDeferred<{ items: Array<typeof rule>; total: number; page: number; pageSize: number }>();
    const filteredRequest = createDeferred<{ items: Array<typeof rule>; total: number; page: number; pageSize: number }>();
    const staleRule = { ...rule, id: 3, name: '旧筛选规则', enabled: true };
    const filteredRule = { ...rule, id: 4, name: '停用规则', enabled: false };
    listRules.mockImplementation((query) => {
      if (query?.enabled === true && query?.pageSize === 100) {
        return Promise.resolve({ items: [rule], total: 1, page: 1, pageSize: 100 });
      }
      if (query?.enabled === false) {
        return filteredRequest.promise;
      }
      if (query?.page === 1 && query?.pageSize === 5 && query?.enabled === undefined) {
        return initialRequest.promise;
      }
      return Promise.resolve({ items: [rule], total: 1, page: 1, pageSize: 5 });
    });

    render(<AlertsPage />);

    fireEvent.change(screen.getByLabelText('启停状态'), { target: { value: 'disabled' } });
    await waitFor(() => expect(listRules).toHaveBeenCalledWith(expect.objectContaining({ enabled: false })));

    filteredRequest.resolve({ items: [filteredRule], total: 1, page: 1, pageSize: 5 });
    expect(await within(await screen.findByRole('table')).findByText('停用规则')).toBeInTheDocument();

    initialRequest.resolve({ items: [staleRule], total: 1, page: 1, pageSize: 5 });
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
