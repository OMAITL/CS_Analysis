import { describe, expect, it } from 'vitest';
import { extractCsItemLabelFromAlertRuleName, formatCsItemAlertTarget } from '../csAlertDisplay';
import type { AlertRuleItem } from '../types/alerts';

describe('csAlertDisplay', () => {
  it('extracts item name from auto alert titles', () => {
    expect(extractCsItemLabelFromAlertRuleName('CS 自动止盈 · AK-47 | 二西莫夫 ≥ 120')).toBe('AK-47 | 二西莫夫');
    expect(extractCsItemLabelFromAlertRuleName('CS 自动止损 · 格洛克 18 型 | 核子花园 (崭新出厂) ≤ 419.08')).toBe(
      '格洛克 18 型 | 核子花园 (崭新出厂)',
    );
  });

  it('formats cs_item target without exposing internal ids', () => {
    const rule = {
      name: 'CS 自动止盈 · AK-47 | 二西莫夫 ≥ 120',
      targetScope: 'cs_item',
      target: '769',
    } as AlertRuleItem;

    expect(formatCsItemAlertTarget(rule)).toBe('AK-47 | 二西莫夫');
  });
});
