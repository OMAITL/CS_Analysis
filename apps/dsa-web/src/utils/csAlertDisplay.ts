import type { AlertRuleItem } from '../types/alerts';

const CS_AUTO_ITEM_NAME_RE = /CS 自动(?:止盈|止损)\s*·\s*(.+?)\s*[≥≤]/;

/** Extract display name from auto-generated CS alert rule titles. */
export function extractCsItemLabelFromAlertRuleName(name: string | null | undefined): string | null {
  if (!name?.trim()) {
    return null;
  }
  const match = name.trim().match(CS_AUTO_ITEM_NAME_RE);
  return match?.[1]?.trim() ?? null;
}

export function formatCsItemAlertTarget(rule: AlertRuleItem): string {
  const fromName = extractCsItemLabelFromAlertRuleName(rule.name);
  if (fromName) {
    return fromName;
  }
  return '单饰品';
}
