import type { CsItemAnalyzeResponse, CsReportPayload } from '../../../types/cs';
import type { CsHomeHistoryItem } from '../../../types/csHome';

export type AdviceTone = 'bullish' | 'bearish' | 'neutral';

const BULLISH_HINTS = ['买', '加仓', '持有', '看多', '利多'];
const BEARISH_HINTS = ['卖', '减仓', '看空', '利空', '不建议', '勿追'];
const NEUTRAL_HINTS = ['观望', '中性', '等待', '震荡'];

export function resolveAdviceTone(advice: string): AdviceTone {
  const text = advice.trim();
  if (BEARISH_HINTS.some((hint) => text.includes(hint))) {
    return 'bearish';
  }
  if (BULLISH_HINTS.some((hint) => text.includes(hint))) {
    return 'bullish';
  }
  if (NEUTRAL_HINTS.some((hint) => text.includes(hint))) {
    return 'neutral';
  }
  return 'neutral';
}

export function adviceToneLabel(tone: AdviceTone): string {
  if (tone === 'bullish') {
    return '看多';
  }
  if (tone === 'bearish') {
    return '看空';
  }
  return '观望';
}

export function formatHistoryDate(iso: string): string {
  try {
    const date = new Date(iso);
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${month}-${day}`;
  } catch {
    return '';
  }
}

export function resolveRiskLevel(score: number): { label: string; tone: AdviceTone } {
  if (score >= 65) {
    return { label: '低风险', tone: 'bullish' };
  }
  if (score >= 40) {
    return { label: '中风险', tone: 'neutral' };
  }
  return { label: '高风险', tone: 'bearish' };
}

export function humanizeAdvice(raw: string): string {
  const text = raw.trim();
  if (!text) {
    return '建议观望，等待更明确信号';
  }
  if (text.includes('观望')) {
    return '建议观望，暂不建议追高';
  }
  if (text.includes('买')) {
    return '可考虑分批买入';
  }
  if (text.includes('卖') || text.includes('减')) {
    return '建议减仓或回避';
  }
  return text;
}

export function buildReportFromData(data: CsItemAnalyzeResponse): CsReportPayload {
  const { trend, report } = data;
  if (report?.summary?.analysisSummary) {
    return report;
  }
  return {
    summary: {
      analysisSummary: trend.signalReasons.slice(0, 2).join('；') || trend.trendStatus,
      operationAdvice: trend.buySignal,
      trendPrediction: trend.trendStatus,
      sentimentScore: trend.signalScore,
    },
    strategy: {
      idealBuy: trend.ma5 ? `约 ${trend.ma5.toFixed(0)}` : undefined,
      secondaryBuy: trend.ma10 ? `约 ${trend.ma10.toFixed(0)}` : undefined,
      stopLoss: trend.ma20 ? `约 ${trend.ma20.toFixed(0)}` : undefined,
      takeProfit: undefined,
    },
    diagnostics: { status: 'unknown', components: {} },
    containers: [],
    belongBoards: [],
  };
}

export function parsePriceNumber(text?: string): number | null {
  if (!text) {
    return null;
  }
  const match = text.replace(/,/g, '').match(/(\d+(?:\.\d+)?)/);
  if (!match) {
    return null;
  }
  const value = Number.parseFloat(match[1]);
  return Number.isFinite(value) ? value : null;
}

export function calcSpreadPct(base: number, compare: number): number | null {
  if (!base || !compare) {
    return null;
  }
  return ((compare - base) / base) * 100;
}

export function stripInternalMarkdown(markdown: string): string {
  return markdown
    .replace(/good_id\s*[:=]\s*\d+/gi, '')
    .replace(/market_hash_name\s*[:=]\s*[^\n]+/gi, '')
    .replace(/cs:\d+/gi, '')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

export function historyCardFromItem(item: CsHomeHistoryItem) {
  const tone = resolveAdviceTone(item.buySignal);
  return {
    id: item.id,
    name: item.itemName,
    score: item.signalScore,
    advice: humanizeAdvice(item.buySignal),
    adviceShort: adviceToneLabel(tone),
    tone,
    date: formatHistoryDate(item.createdAt),
  };
}

export const HOT_ITEM_PRESETS = [
  { label: '蝴蝶刀 北方森林', query: '蝴蝶刀 北方森林' },
  { label: 'AK-47 火蛇', query: 'AK-47 火蛇' },
  { label: '爪子刀 多普勒', query: '爪子刀 多普勒' },
  { label: 'M4A4 龙王', query: 'M4A4 龙王' },
] as const;

export const QUICK_EXAMPLES = [
  '蝴蝶刀 北方森林',
  'AK47 火蛇',
  '爪子刀 多普勒',
  'M4A4 龙王',
] as const;
