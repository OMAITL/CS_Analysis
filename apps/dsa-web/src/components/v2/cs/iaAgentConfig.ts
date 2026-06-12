import type { LucideIcon } from 'lucide-react';
import {
  BarChart3,
  Brain,
  FileText,
  Globe,
  Newspaper,
  Search,
  Wrench,
} from 'lucide-react';

export type AgentPipelineStepId =
  | 'identify'
  | 'market'
  | 'technical'
  | 'intel'
  | 'strategy'
  | 'report';

export type AgentPipelineStep = {
  id: AgentPipelineStepId;
  label: string;
  description: string;
  tool: string;
  icon: LucideIcon;
};

/** Mirrors the real CS analyze pipeline in `CSItemService.analyze_item`. */
export const AGENT_PIPELINE_STEPS: AgentPipelineStep[] = [
  {
    id: 'identify',
    label: '饰品识别',
    description: '模糊搜索并锁定具体饰品',
    tool: 'CSQAQ item search',
    icon: Search,
  },
  {
    id: 'market',
    label: '行情融合',
    description: '开放 API + 爬虫库，多平台价格快照',
    tool: 'ItemOhlcvBuilder',
    icon: Globe,
  },
  {
    id: 'technical',
    label: '技术分析',
    description: 'K 线、均线、RSI 与趋势信号打分',
    tool: 'run_cs_item_analysis',
    icon: BarChart3,
  },
  {
    id: 'intel',
    label: '事件情报',
    description: 'Major、武器箱、HLTV、贴吧等舆论检索',
    tool: 'fetch_cs_event_intel',
    icon: Newspaper,
  },
  {
    id: 'strategy',
    label: '策略决策',
    description: '注入交易 Skill，输出结构化 JSON 仪表盘',
    tool: 'run_cs_item_llm_analysis',
    icon: Brain,
  },
  {
    id: 'report',
    label: '报告生成',
    description: '结论、点位、风险提示与 Markdown 全文',
    tool: 'build_cs_report_payload',
    icon: FileText,
  },
];

export const AGENT_DATA_SOURCES = [
  { id: 'csqaq', label: 'CSQAQ', hint: '行情 / 搜索' },
  { id: 'yyyp', label: '悠悠有品', hint: '国内成交价' },
  { id: 'buff', label: 'BUFF', hint: '国内平台' },
  { id: 'steam', label: 'Steam', hint: '国际参考价' },
  { id: 'crawl', label: '爬虫库', hint: '历史 K 线' },
  { id: 'search', label: '事件搜索', hint: 'HLTV / 贴吧' },
] as const;

export type AgentPresetTask = {
  id: string;
  title: string;
  query: string;
  focus: string;
  /** Auto-pick analysis skill so users do not need to choose manually. */
  skillId?: string;
  skillHint?: string;
};

export const AGENT_PRESET_TASKS: AgentPresetTask[] = [
  {
    id: 'butterfly',
    title: '蝴蝶刀 北方森林',
    query: '蝴蝶刀 北方森林',
    focus: '低价位刀类 · 流动性观察',
    skillId: 'liquidity_gate',
    skillHint: '流动性门槛',
  },
  {
    id: 'fireserpent',
    title: 'AK-47 火蛇',
    query: 'AK-47 火蛇',
    focus: '经典步枪 · 长线趋势',
    skillId: 'bull_trend',
    skillHint: '多头趋势',
  },
  {
    id: 'doppler',
    title: '爪子刀 多普勒',
    query: '爪子刀 多普勒',
    focus: '高波动 · 套利空间',
    skillId: 'platform_arbitrage',
    skillHint: '跨平台价差',
  },
  {
    id: 'dragon',
    title: 'M4A4 龙王',
    query: 'M4A4 龙王',
    focus: '事件驱动 · 箱价联动',
    skillId: 'event_driven',
    skillHint: '事件驱动',
  },
];

export const AGENT_TOOL_FALLBACK = {
  id: 'tools',
  label: 'Agent 工具链',
  icon: Wrench,
};
