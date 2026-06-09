import { describe, expect, it } from 'vitest';
import type { AlertRuleItem } from '../../types/alerts';
import {
  buildHoldingLookup,
  buildTodayActivity,
  computeDistanceToTrigger,
  formatDistanceDisplay,
  enrichAlertRule,
  pickImportantRulesByItem,
  pickTopInsightItem,
  priorityFromDistance,
  resolvePriceActionLabel,
  resolveRuleScopeLabel,
  resolveTargetPrice,
  ruleMatchesSearch,
  shouldShowInsightPriceBadge,
  sortEnrichedRules,
} from '../csAlertMonitor';

const baseRule = {
  id: 1,
  name: 'CS 自动止损 · AK-47 | 二西莫夫 (久经沙场) ≤ 419.08',
  targetScope: 'cs_item',
  target: '769',
  alertType: 'cs_price_cross',
  parameters: { direction: 'below', price: 419.08, platform: 'yyyp' },
  severity: 'warning',
  enabled: true,
  source: 'cs_auto',
} as AlertRuleItem;

describe('csAlertMonitor', () => {
  it('computes stop-loss distance and priority', () => {
    const result = computeDistanceToTrigger(419.08, 438.77, 'below');
    expect(result.distancePct).toBeCloseTo(4.7, 1);
    expect(result.isAtOrPastTarget).toBe(false);
    expect(priorityFromDistance(result.distancePct)).toBe('watch');
  });

  it('shows 0.0% when target is already breached', () => {
    const takeProfit = computeDistanceToTrigger(558.77, 807.98, 'above');
    expect(takeProfit.isAtOrPastTarget).toBe(true);
    expect(takeProfit.distancePct).toBe(0);
    expect(formatDistanceDisplay(takeProfit.distancePct)).toBe('0.0%');

    const stopLoss = computeDistanceToTrigger(17434.46, 14400, 'below');
    expect(stopLoss.isAtOrPastTarget).toBe(true);
    expect(stopLoss.distancePct).toBe(0);
    expect(formatDistanceDisplay(stopLoss.distancePct)).toBe('0.0%');
  });

  it('resolves target price from auto rule name', () => {
    expect(resolveTargetPrice(baseRule)).toBe(419.08);
  });

  it('resolves price action labels for auto take-profit and stop-loss rules', () => {
    expect(resolvePriceActionLabel(baseRule)).toBe('止损');
    expect(resolvePriceActionLabel({
      ...baseRule,
      name: 'CS 自动止盈 · AK-47 | 二西莫夫 ≥ 500',
      parameters: { direction: 'above', price: 500, platform: 'yyyp' },
    })).toBe('止盈');
  });

  it('enriches cs_item rules with holdings snapshot', () => {
    const holdings = buildHoldingLookup([
      {
        goodId: 769,
        platform: 'yyyp',
        itemName: 'AK-47 | 二西莫夫 (久经沙场)',
        quantity: 2,
        purchasePrice: 400,
        marketPrice: 438.77,
        pnlPct: 9.7,
      },
    ]);
    const enriched = enrichAlertRule(baseRule, holdings);
    expect(enriched.priceActionLabel).toBe('止损');
    expect(enriched.scopeLabel).toBe('单品');
    expect(enriched.displayName).toContain('AK-47');
    expect(enriched.currentPrice).toBe(438.77);
    expect(enriched.holding?.quantity).toBe(2);
    expect(enriched.priority).toBe('watch');
    expect(enriched.aiAdvice.suggestion).toBeTruthy();
  });

  it('matches search query against item and portfolio rule names', () => {
    const holdings = buildHoldingLookup([
      {
        goodId: 769,
        platform: 'yyyp',
        itemName: 'AK-47 | 二西莫夫 (久经沙场)',
        marketPrice: 438.77,
      },
    ]);
    const itemRule = enrichAlertRule(baseRule, holdings);
    const portfolioRule = enrichAlertRule(
      {
        ...baseRule,
        id: 9,
        name: 'CS 自动止损监控',
        targetScope: 'cs_holdings',
        target: 'all',
        alertType: 'cs_stop_loss',
        parameters: { mode: 'near' },
      },
      holdings,
    );

    expect(resolveRuleScopeLabel(itemRule.rule)).toBe('单品');
    expect(resolveRuleScopeLabel(portfolioRule.rule)).toBe('全仓');
    expect(ruleMatchesSearch(itemRule, '二西莫夫')).toBe(true);
    expect(ruleMatchesSearch(portfolioRule, '止损监控')).toBe(true);
    expect(ruleMatchesSearch(itemRule, '格洛克')).toBe(false);
  });

  it('sorts urgent rules ahead of normal rules', () => {
    const urgent = enrichAlertRule(baseRule, buildHoldingLookup([{ goodId: 769, platform: 'yyyp', marketPrice: 420 }]));
    const normal = enrichAlertRule(
      {
        ...baseRule,
        id: 2,
        parameters: { direction: 'below', price: 300, platform: 'yyyp' },
      },
      buildHoldingLookup([{ goodId: 769, platform: 'yyyp', marketPrice: 438.77 }]),
    );
    const sorted = sortEnrichedRules([normal, urgent]);
    expect(sorted[0]?.priority).toBe('urgent');
  });

  it('does not suggest profit lock for stop-loss rules far from trigger', () => {
    const holdings = buildHoldingLookup([
      {
        goodId: 769,
        platform: 'yyyp',
        marketPrice: 906,
        purchasePrice: 743,
        pnlPct: 21.9,
      },
    ]);
    const stopLoss = enrichAlertRule(
      {
        ...baseRule,
        parameters: { direction: 'below', price: 668.7, platform: 'yyyp' },
      },
      holdings,
    );
    expect(stopLoss.aiAdvice.suggestion).not.toMatch(/锁定部分利润/);
    expect(stopLoss.aiAdvice.suggestion).toMatch(/高于止损线|继续观察/);
  });

  it('prefers breached take-profit rules for top insight', () => {
    const holdings = buildHoldingLookup([
      {
        goodId: 769,
        platform: 'yyyp',
        marketPrice: 906,
        purchasePrice: 743,
        pnlPct: 21.9,
      },
    ]);
    const stopLoss = enrichAlertRule(
      {
        ...baseRule,
        parameters: { direction: 'below', price: 668.7, platform: 'yyyp' },
      },
      holdings,
    );
    const takeProfit = enrichAlertRule(
      {
        ...baseRule,
        id: 2,
        name: 'CS 自动止盈 · AK-47 | 传承 ≥ 891.6',
        parameters: { direction: 'above', price: 891.6, platform: 'yyyp' },
        cooldownActive: true,
      },
      holdings,
    );
    const top = pickTopInsightItem([stopLoss, takeProfit]);
    expect(top?.rule.id).toBe(2);
    expect(top?.priceActionLabel).toBe('止盈');
    expect(shouldShowInsightPriceBadge(top!)).toBe(true);
  });

  it('hides insight badge when stop-loss label conflicts with profit suggestion', () => {
    const conflicting = enrichAlertRule(baseRule, buildHoldingLookup([
      { goodId: 769, platform: 'yyyp', marketPrice: 906, purchasePrice: 743, pnlPct: 21.9 },
    ]));
    const patched = {
      ...conflicting,
      aiAdvice: { ...conflicting.aiAdvice, suggestion: '盈利较好，可考虑锁定部分利润' },
    };
    expect(shouldShowInsightPriceBadge(patched)).toBe(false);
  });

  it('deduplicates important alerts for the same item', () => {
    const holdings = buildHoldingLookup([
      { goodId: 769, platform: 'yyyp', marketPrice: 420, itemName: 'AK-47 | 二西莫夫' },
    ]);
    const stopLoss = enrichAlertRule(baseRule, holdings);
    const takeProfit = enrichAlertRule(
      {
        ...baseRule,
        id: 2,
        name: 'CS 自动止盈 · AK-47 | 二西莫夫 ≥ 500',
        parameters: { direction: 'above', price: 500, platform: 'yyyp' },
      },
      holdings,
    );
    const picked = pickImportantRulesByItem([takeProfit, stopLoss], 6);
    expect(picked).toHaveLength(1);
    expect(picked[0]?.rule.id).toBe(baseRule.id);
  });

  it('aggregates same-minute rule creation activity', () => {
    const today = new Date().toISOString().slice(0, 10);
    const createdAt = `${today}T12:43:00`;
    const rules = [1, 2, 3].map((id) => ({
      ...baseRule,
      id,
      name: `CS 自动止损 · Item ${id}`,
      createdAt,
    }));

    const activity = buildTodayActivity([], rules);
    expect(activity).toHaveLength(1);
    expect(activity[0]?.title).toBe('批量新增 3 条监控规则');
  });
});
