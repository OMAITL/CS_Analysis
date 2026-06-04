export type CsKlineBar = {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number | null;
  amount?: number | null;
  changePercent?: number | null;
};

export type CsItemSnapshot = {
  name?: string;
  marketHashName?: string;
  buffSellPrice?: number;
  yyypSellPrice?: number;
  steamSellPrice?: number;
  buffSellNum?: number;
  yyypSellNum?: number;
  turnoverNumber?: number;
  updatedAt?: string;
};

export type CsItemMeta = {
  goodId: number;
  itemName: string;
  marketHashName: string;
  platform: string | number;
  ohlcSource: string;
  volumeSource: string;
  dataQuality: string;
  rowCount: number;
  crawlRows: number;
  apiRows: number;
  periodDays: number;
};

export type CsItemTrend = {
  code: string;
  trendStatus: string;
  maAlignment: string;
  currentPrice: number;
  ma5: number;
  ma10: number;
  ma20: number;
  ma60: number;
  biasMa5: number;
  volumeStatus: string;
  volumeRatio5d: number;
  buySignal: string;
  signalScore: number;
  signalReasons: string[];
  riskFactors: string[];
  macdStatus: string;
  rsiStatus: string;
  macdDif: number;
  macdDea: number;
  rsi12: number;
};

export type CsEventIntelItem = {
  title: string;
  snippet?: string;
  url?: string;
  dimension?: string;
  source?: string;
  publishedDate?: string;
  relevance?: 'direct' | 'case' | 'market' | 'drop';
};

export type CsItemContainer = {
  name: string;
  goodId?: number;
  price?: number;
};

export type CsReportBoard = {
  name: string;
  type?: string;
  code?: string;
};

export type CsReportDiagnosticComponent = {
  key?: string;
  label?: string;
  status?: string;
  message?: string;
};

export type CsReportSummaryBlock = {
  analysisSummary: string;
  operationAdvice: string;
  trendPrediction: string;
  sentimentScore: number;
};

export type CsReportStrategyBlock = {
  idealBuy?: string;
  secondaryBuy?: string;
  stopLoss?: string;
  takeProfit?: string;
};

export type CsReportDiagnosticsBlock = {
  status?: string;
  statusLabel?: string;
  reason?: string;
  components?: Record<string, CsReportDiagnosticComponent>;
  copyText?: string;
};

export type CsReportPayload = {
  summary: CsReportSummaryBlock;
  strategy: CsReportStrategyBlock;
  diagnostics: CsReportDiagnosticsBlock;
  containers: CsItemContainer[];
  belongBoards: CsReportBoard[];
};

export type CsGoodIdItem = {
  goodId: number;
  name: string;
  marketHashName: string;
};

export type CsItemSearchResponse = {
  items: CsGoodIdItem[];
  pageIndex: number;
  pageSize: number;
  total: number;
};

export type CsItemSearchRequest = {
  search: string;
  pageIndex?: number;
  pageSize?: number;
};

export type CsItemAnalyzeRequest = {
  goodId?: number;
  item?: string;
  platform?: string;
  period?: number;
  preferCrawl?: boolean;
  refreshCrawl?: boolean;
  refreshToday?: boolean;
  klinePages?: number;
  includeReport?: boolean;
  skills?: string[];
};

export type CsItemAnalyzeResponse = {
  goodId: number;
  itemName: string;
  marketHashName: string;
  platform: string;
  snapshot: CsItemSnapshot;
  meta: CsItemMeta;
  trend: CsItemTrend;
  ohlcv: CsKlineBar[];
  reportMarkdown: string;
  reportSource: 'llm' | 'template' | 'none';
  report?: CsReportPayload;
  eventIntel?: CsEventIntelItem[];
  eventContext?: string;
  activeSkills?: string[];
};
