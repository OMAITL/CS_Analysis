import type { CsItemAnalyzeResponse, CsReportPayload } from '../../../types/cs';
import type { CsHomeHistoryItem } from '../../../types/csHome';

export type AdviceTone = 'bullish' | 'bearish' | 'neutral';

const BULLISH_HINTS = ['买', '加仓', '持有', '看多', '利多'];
const BEARISH_HINTS = ['卖', '减仓', '看空', '利空', '不建议', '勿追'];
const NEUTRAL_HINTS = ['观望', '中性', '等待', '震荡'];

const CS_PLATFORM_LABELS: Record<string, string> = {
  yyyp: '悠悠有品',
  buff: 'BUFF',
  steam: 'Steam',
};

const BEARISH_SIGNAL_HINTS = [
  '空头',
  '下跌',
  '死叉',
  '不宜做多',
  '严禁追高',
  '破位',
  '放量下跌',
  '转弱',
  '下穿',
  '超买',
];

export function formatCsPlatformLabel(platform: string): string {
  const key = (platform || '').trim().toLowerCase();
  return CS_PLATFORM_LABELS[key] ?? platform.toUpperCase();
}

export function isBearishSignalLine(line: string): boolean {
  const text = line.trim();
  if (!text) {
    return false;
  }
  if (/^⚠️?/.test(text) && BEARISH_SIGNAL_HINTS.some((hint) => text.includes(hint))) {
    return true;
  }
  return BEARISH_SIGNAL_HINTS.some((hint) => text.includes(hint));
}

export function splitTrendSignals(signalReasons: string[], riskFactors: string[]) {
  const bullish: string[] = [];
  const bearish = [...(riskFactors ?? [])];
  for (const line of signalReasons ?? []) {
    if (isBearishSignalLine(line)) {
      if (!bearish.includes(line)) {
        bearish.push(line);
      }
      continue;
    }
    bullish.push(line);
  }
  return { bullish, bearish };
}

export function stripMarkdownInline(text: string): string {
  return text
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/\*([^*]+)\*/g, '$1')
    .trim();
}

export function humanizeTrendLine(line: string): string {
  return stripMarkdownInline(line)
    .replace(/^[✅⚡⭐❌⚠️⚠✓\s]+/, '')
    .replace(/\bMA5\b/g, '5日均线')
    .replace(/\bMA10\b/g, '10日均线')
    .replace(/\bMA20\b/g, '20日均线')
    .replace(/\bRSI\b/g, '强弱指标')
    .replace(/\bMACD\b/g, '趋势指标')
    .replace(/YYYP/gi, '悠悠有品')
    .trim();
}

export function humanizeCsReportSection(text: string): string {
  return stripMarkdownInline(text)
    .replace(/YYYP/gi, '悠悠有品')
    .replace(/\bMA5\b/g, '5日均线')
    .replace(/\bMA10\b/g, '10日均线')
    .replace(/\bMA20\b/g, '20日均线')
    .replace(/未持仓/g, '尚未持有')
    .replace(/已持仓/g, '已经持有')
    .replace(/本报告由 LLM.*$/g, '')
    .replace(/market_hash_name.*$/gi, '')
    .replace(/good_id.*$/gi, '')
    .replace(
      /符合默认多头趋势策略，满足.*?买入条件。?/,
      '当前价格趋势偏多，尚未明显偏离短期均线，可按计划分批布局。',
    )
    .replace(/现价相对5日均线乖离率.*?，/g, '')
    .replace(/量能正常无异常，/g, '成交量表现正常，')
    .trim();
}

export function extractMarkdownSection(markdown: string, heading: string): string {
  const regex = new RegExp(`##\\s*${heading}\\s*\\n+([\\s\\S]*?)(?=\\n##\\s|$)`, 'i');
  return markdown.match(regex)?.[1]?.trim() ?? '';
}

function humanizeBuyReason(text: string): string {
  const raw = stripMarkdownInline(text).replace(/^分析依据[：:]\s*/, '').replace(/^理由[：:]\s*/, '');
  if (/MA5|MA10|MA20|乖离|多头趋势策略|均线结构/.test(raw)) {
    return '价格趋势偏多，与短期均线关系健康，可按计划分批操作；若跌破止损位应及时减仓。';
  }
  return humanizeCsReportSection(raw);
}

function humanizeWatchFallback(data: CsItemAnalyzeResponse, report: CsReportPayload): ReportSummaryBlock {
  const advice = humanizeAdvice(report.summary.operationAdvice || data.trend.buySignal);
  return {
    lead: `${advice}。`,
    items: [{ text: '建议持续关注成交量与各平台价差，避免盲目追高。' }],
  };
}

export type ReportSummaryPoint = {
  label?: string;
  text: string;
};

export type ReportSummaryBlock = {
  lead?: string;
  items: ReportSummaryPoint[];
};

function cleanAdvicePhrase(text: string): string {
  return humanizeCsReportSection(text)
    .replace(/^(空仓者建议|持仓者建议)[：:]\s*/, '')
    .replace(/^(建议)[：:]\s*/, '')
    .trim();
}

function parseLabeledPoint(line: string): ReportSummaryPoint | null {
  const cleaned = humanizeCsReportSection(line.replace(/^[-*]\s*/, ''));
  const match = cleaned.match(/^(尚未持有|已经持有|理想买入|止损|目标|分析依据)[：:]\s*(.+)$/);
  if (!match) {
    return null;
  }
  let text = cleanAdvicePhrase(match[2]);
  if (match[1] === '止损') {
    text = text
      .replace(/^止损[：:]\s*/, '')
      .replace(/^止损位[：:]\s*/, '')
      .trim();
  }
  return { label: match[1], text };
}

function splitInlinePositionAdvice(text: string): ReportSummaryBlock {
  const normalized = humanizeCsReportSection(text);
  const leadMatch = normalized.match(/^(.+?)(?=尚未持有[：:]|已经持有[：:])/);
  const lead = leadMatch?.[1]?.trim() ?? '';
  const items: ReportSummaryPoint[] = [];

  const noPos = normalized.match(/尚未持有[：:]\s*(.+?)(?=已经持有[：:]|$)/);
  const hasPos = normalized.match(/已经持有[：:]\s*(.+)$/);
  if (noPos) {
    items.push({ label: '尚未持有', text: cleanAdvicePhrase(noPos[1]) });
  }
  if (hasPos) {
    items.push({ label: '已经持有', text: cleanAdvicePhrase(hasPos[1]) });
  }

  if (!lead && items.length === 0) {
    return { lead: normalized, items: [] };
  }
  return { lead: lead || undefined, items };
}

function parseConclusionBlock(coreRaw: string, fallback: string): ReportSummaryBlock {
  if (!coreRaw.trim()) {
    return { lead: fallback, items: [] };
  }

  const lines = coreRaw.split('\n').map((line) => line.trim()).filter(Boolean);
  let lead = '';
  const items: ReportSummaryPoint[] = [];

  for (const line of lines) {
    const point = parseLabeledPoint(line);
    if (point) {
      items.push(point);
      continue;
    }
    const cleaned = humanizeCsReportSection(line.replace(/^[-*]\s*/, ''));
    if (/尚未持有[：:]|已经持有[：:]/.test(cleaned)) {
      const split = splitInlinePositionAdvice(cleaned);
      if (split.lead && !lead) {
        lead = split.lead;
      }
      items.push(...split.items);
      continue;
    }
    if (!lead) {
      lead = cleaned;
    } else {
      items.push({ text: cleaned });
    }
  }

  if (!lead && items.length === 0) {
    return splitInlinePositionAdvice(fallback);
  }
  return { lead: lead || undefined, items };
}

function parseRiskBlock(riskRaw: string, fallbackItems: string[]): ReportSummaryBlock {
  if (!riskRaw.trim()) {
    const text = fallbackItems.join('；');
    return text
      ? { items: [{ text }] }
      : { lead: '饰品价格波动通常高于传统资产，请注意控制仓位，并关注各平台流动性。', items: [] };
  }

  const lines = riskRaw
    .split('\n')
    .map((line) => humanizeCsReportSection(line.replace(/^[-*]\s*/, '')).trim())
    .filter(Boolean);

  if (lines.length > 1) {
    return { items: lines.map((text) => ({ text })) };
  }

  const paragraph = lines[0] ?? '';
  const sentences = paragraph
    .split(/(?<=[。！？])\s*/)
    .map((part) => part.trim())
    .filter(Boolean);

  if (sentences.length > 1) {
    return { items: sentences.map((text) => ({ text })) };
  }

  return { lead: paragraph, items: [] };
}

function parseWatchBlock(watchRaw: string, fallback: ReportSummaryBlock): ReportSummaryBlock {
  if (!watchRaw.trim()) {
    return fallback;
  }

  let lead = '';
  const items: ReportSummaryPoint[] = [];

  for (const line of watchRaw.split('\n').map((item) => item.trim()).filter(Boolean)) {
    if (/^\*\*理由\*\*/.test(line) || /^理由[：:]/.test(stripMarkdownInline(line))) {
      items.push({ label: '分析依据', text: humanizeBuyReason(line) });
      continue;
    }
    if (/MA5≥|MA10≥|MA20≥|多头趋势策略/.test(line)) {
      continue;
    }

    const cleaned = humanizeCsReportSection(line.replace(/^[-*]\s*/, ''));
    const segments = cleaned.split(/\s*(?=(?:理想买入|止损|目标|分析依据)[：:])/).filter(Boolean);
    if (segments.length > 1) {
      for (const segment of segments) {
        const segmentPoint = parseLabeledPoint(segment);
        if (segmentPoint) {
          items.push(segmentPoint);
        }
      }
      continue;
    }

    const point = parseLabeledPoint(line);
    if (point) {
      items.push(point);
      continue;
    }

    if (/^(理想买入|止损|目标|分析依据)[：:]/.test(cleaned)) {
      const inlinePoint = parseLabeledPoint(cleaned);
      if (inlinePoint) {
        items.push(inlinePoint);
        continue;
      }
    }

    if (!lead && !/^[-*]/.test(line)) {
      lead = cleaned;
    } else {
      items.push({ text: cleaned });
    }
  }

  if (items.length === 0 && !lead) {
    return splitInlinePositionAdvice(watchRaw);
  }
  return { lead: lead || undefined, items };
}

function processReportMarkdownLine(trimmed: string): string[] {
  if (/^##\s|^###\s|^---+$/.test(trimmed)) {
    return [trimmed];
  }

  const listMatch = trimmed.match(/^[-*]\s*(.+)$/);
  if (listMatch) {
    const item = listMatch[1].replace(/^[✅⚡⭐❌⚠️⚠✓]+\s*/, '').trim();
    return [`- ${item}`];
  }

  const boldOnly = trimmed.match(/^\*\*([^*]+)\*\*\.?\s*$/);
  if (boldOnly) {
    return [`### ${boldOnly[1].trim()}`];
  }

  const boldColon = trimmed.match(/^\*\*([^*]+)\*\*[：:]\s*(.+)$/);
  if (boldColon) {
    return [`### ${boldColon[1].trim()}`, '', boldColon[2].trim()];
  }

  const boldLead = trimmed.match(/^\*\*([^*]{1,28})\*\*\s+(.+)$/);
  if (boldLead) {
    return [`### ${boldLead[1].trim()}`, '', boldLead[2].trim()];
  }

  return [trimmed];
}

function expandDenseLine(line: string): string[] {
  if (line.length < 72 || /^[-*#>]/.test(line)) {
    return [line];
  }

  const sentences = line.match(/[^。；]+[。；]+/g)?.map((part) => part.trim()).filter(Boolean);
  if (!sentences || sentences.length < 2) {
    return [line];
  }
  if (sentences.some((part) => part.length > 140)) {
    return [line];
  }

  return sentences.map((part) => `- ${part}`);
}

function expandDenseTextBlock(block: string): string {
  const lines = block.split('\n');
  const expanded: string[] = [];

  for (const line of lines) {
    if (!line.trim()) {
      continue;
    }
    if (/^[-*#>]/.test(line.trim())) {
      expanded.push(line);
      continue;
    }
    expanded.push(...expandDenseLine(line));
  }

  return expanded.join('\n');
}

export function normalizeReportMarkdownStructure(md: string): string {
  const normalizedLines: string[] = [];
  for (const rawLine of md.split('\n')) {
    const trimmed = rawLine.trim();
    if (!trimmed) {
      normalizedLines.push('');
      continue;
    }
    normalizedLines.push(...processReportMarkdownLine(trimmed));
  }

  const blocks: string[] = [];
  let current: string[] = [];

  const flush = () => {
    if (current.length === 0) {
      return;
    }
    blocks.push(expandDenseTextBlock(current.join('\n')));
    current = [];
  };

  for (const line of normalizedLines) {
    if (line === '') {
      flush();
      continue;
    }
    if (/^##\s/.test(line) || /^###\s/.test(line)) {
      flush();
      blocks.push(line);
      continue;
    }
    current.push(line);
  }
  flush();

  return blocks.join('\n\n').replace(/\n{3,}/g, '\n\n').trim();
}

export function humanizeCsReportMarkdown(raw: string): string {
  if (!raw.trim()) {
    return '';
  }
  let md = raw;
  md = md.replace(/^#\s[^\n]+\n+/m, '');
  md = md.replace(/^-\s+\*\*market_hash_name\*\*.*\n/gm, '');
  md = md.replace(/^-\s+\*\*good_id\*\*.*\n/gm, '');
  md = md.replace(/^-\s+\*\*(?:主平台|参考平台)\*\*.*\n/gm, '');
  md = md.replace(/^-\s+\*\*综合评分\*\*.*\n/gm, '');
  md = md.replace(/^-\s+\*\*数据质量\*\*.*\n/gm, '');
  md = md.replace(/^>\s*本报告由 LLM.*\n+/gm, '');
  md = md.replace(/\*\*未持仓\*\*[：:]/g, '**尚未持有**：');
  md = md.replace(/\*\*已持仓\*\*[：:]/g, '**已经持有**：');
  md = md.replace(/\*\*理由\*\*[：:]/g, '**分析依据**：');
  md = md.replace(/YYYP/gi, '悠悠有品');
  md = md.replace(/\bMA5\b/g, '5日均线');
  md = md.replace(/\bMA10\b/g, '10日均线');
  md = md.replace(/\bMA20\b/g, '20日均线');
  md = md.replace(/^(\s*[-*]\s*)[✅⚡⭐❌⚠️⚠✓]+\s*/gm, '$1');
  return normalizeReportMarkdownStructure(md);
}

export function buildUserFacingReportSections(data: CsItemAnalyzeResponse) {
  const report = buildReportFromData(data);
  const raw = stripInternalMarkdown(data.reportMarkdown || '');
  const coreRaw = extractMarkdownSection(raw, '核心结论');
  const riskRaw = extractMarkdownSection(raw, '风险提示');
  const watchRaw = extractMarkdownSection(raw, '操作建议');

  const fallbackConclusion = humanizeCsReportSection(
    report.summary.analysisSummary
    || humanizeAdvice(report.summary.operationAdvice || data.trend.buySignal),
  );

  const conclusion = parseConclusionBlock(coreRaw, fallbackConclusion);

  const { bearish } = splitTrendSignals(data.trend.signalReasons ?? [], data.trend.riskFactors ?? []);
  const risks = parseRiskBlock(
    riskRaw,
    bearish.slice(0, 3).map(humanizeTrendLine),
  );

  const watch = parseWatchBlock(watchRaw, humanizeWatchFallback(data, report));

  return {
    conclusion,
    risks,
    watch,
    expandedMarkdown: humanizeCsReportMarkdown(raw),
  };
}

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
