import type { CsSkillInfo } from '../types/csHome';

export const CS_SKILL_CATEGORY_FALLBACK: Record<string, string> = {
  cs_native: '饰品专属',
  trend: '趋势',
  pattern: '形态',
  reversal: '反转',
  framework: '框架',
};

export const CS_RECOMMENDED_SKILL_IDS_FALLBACK = [
  'bull_trend',
  'event_driven',
  'platform_arbitrage',
  'liquidity_gate',
  'manipulation_radar',
] as const;

export type CsSkillGroup = {
  key: string;
  label: string;
  items: CsSkillInfo[];
};

const CATEGORY_ORDER = ['cs_native', 'framework', 'trend', 'pattern', 'reversal'] as const;

export function resolveCategoryLabels(
  apiLabels?: Record<string, string>,
): Record<string, string> {
  return { ...CS_SKILL_CATEGORY_FALLBACK, ...(apiLabels ?? {}) };
}

export function groupCsSkills(
  skills: CsSkillInfo[],
  options?: {
    recommendedIds?: string[];
    categoryLabels?: Record<string, string>;
    includeRecommendedGroup?: boolean;
  },
): CsSkillGroup[] {
  const labels = resolveCategoryLabels(options?.categoryLabels);
  const recommendedSet = new Set(options?.recommendedIds ?? CS_RECOMMENDED_SKILL_IDS_FALLBACK);
  const groups: CsSkillGroup[] = [];

  if (options?.includeRecommendedGroup !== false) {
    const recommended = skills.filter((skill) => recommendedSet.has(skill.id));
    if (recommended.length > 0) {
      groups.push({
        key: 'recommended',
        label: '推荐（新手优先）',
        items: recommended,
      });
    }
  }

  const used = new Set(groups.flatMap((group) => group.items.map((item) => item.id)));

  for (const category of CATEGORY_ORDER) {
    const items = skills.filter(
      (skill) => skill.category === category && !used.has(skill.id),
    );
    if (items.length === 0) {
      continue;
    }
    groups.push({
      key: category,
      label: labels[category] ?? category,
      items,
    });
    items.forEach((item) => used.add(item.id));
  }

  const rest = skills.filter((skill) => !used.has(skill.id));
  if (rest.length > 0) {
    groups.push({
      key: 'other',
      label: '其他',
      items: rest,
    });
  }

  return groups;
}

export function findCsSkill(
  skills: CsSkillInfo[],
  skillId: string,
): CsSkillInfo | undefined {
  return skills.find((skill) => skill.id === skillId);
}

export function resolveSkillDisplayName(
  skills: CsSkillInfo[],
  skillId: string,
  emptyLabel = '智能默认',
): string {
  if (!skillId) {
    return emptyLabel;
  }
  return findCsSkill(skills, skillId)?.displayName ?? skillId;
}
