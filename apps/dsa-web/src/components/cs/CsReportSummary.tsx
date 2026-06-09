import type React from 'react';
import type {
  ReportDetails,
  ReportMeta,
  ReportSummary as ReportSummaryType,
  RunDiagnosticSummary,
} from '../../types/analysis';
import type { CsItemAnalyzeResponse, CsReportPayload } from '../../types/cs';
import { Button } from '../common';
import { ReportDiagnostics } from '../report/ReportDiagnostics';
import { ReportOverview } from '../report/ReportOverview';
import { ReportStrategy } from '../report/ReportStrategy';
import { CsPlatformPrices } from './CsPlatformPrices';
import { CsReportMarkdown } from './CsReportMarkdown';
import { CsReportNews } from './CsReportNews';
import { CsTechnicalPanel } from './CsTechnicalPanel';

type CsReportSummaryProps = {
  data: CsItemAnalyzeResponse;
  onReanalyze?: () => void;
  isAnalyzing?: boolean;
};

function buildFallbackReport(data: CsItemAnalyzeResponse): CsReportPayload {
  const { trend } = data;
  return {
    summary: {
      analysisSummary: trend.signalReasons.slice(0, 2).join('；') || `${trend.trendStatus}，信号 ${trend.buySignal}`,
      operationAdvice: trend.buySignal || '观望',
      trendPrediction: trend.trendStatus || '震荡',
      sentimentScore: trend.signalScore || 0,
    },
    strategy: {
      idealBuy: trend.ma5 ? `MA5 附近 ${trend.ma5.toFixed(2)}` : undefined,
      secondaryBuy: trend.ma10 ? `MA10 附近 ${trend.ma10.toFixed(2)}` : undefined,
      stopLoss: trend.ma20 ? `跌破 MA20 ${trend.ma20.toFixed(2)}` : undefined,
    },
    diagnostics: {
      status: data.meta.dataQuality === 'full' ? 'normal' : 'degraded',
      statusLabel: data.meta.dataQuality === 'full' ? '正常' : '部分降级',
      reason: `数据质量 ${data.meta.dataQuality}，OHLC 来源 ${data.meta.ohlcSource}`,
      components: {},
      copyText: '',
    },
    containers: [],
    belongBoards: [],
  };
}

function toRunDiagnosticSummary(report: CsReportPayload): RunDiagnosticSummary {
  const components: RunDiagnosticSummary['components'] = {};
  for (const [key, value] of Object.entries(report.diagnostics.components || {})) {
    components[key] = {
      key: value.key || key,
      label: value.label || key,
      status: value.status as RunDiagnosticSummary['components'][string]['status'],
      message: value.message || '',
    };
  }
  return {
    status: (report.diagnostics.status as RunDiagnosticSummary['status']) || 'unknown',
    statusLabel: report.diagnostics.statusLabel || '',
    reason: report.diagnostics.reason || '',
    components,
    copyText: report.diagnostics.copyText || '',
  };
}

export const CsReportSummary: React.FC<CsReportSummaryProps> = ({
  data,
  onReanalyze,
  isAnalyzing = false,
}) => {
  const report = data.report ?? buildFallbackReport(data);
  const lastBar = data.ohlcv[data.ohlcv.length - 1];
  const changePct = lastBar?.changePercent ?? undefined;
  const price = data.trend.currentPrice || lastBar?.close;

  const meta: ReportMeta = {
    queryId: `cs-${data.itemName}`,
    stockCode: data.itemName,
    stockName: data.itemName,
    reportType: 'detailed',
    reportLanguage: 'zh',
    createdAt: new Date().toISOString(),
    currentPrice: price,
    changePct: changePct ?? undefined,
  };

  const summary: ReportSummaryType = {
    analysisSummary: report.summary.analysisSummary,
    operationAdvice: report.summary.operationAdvice,
    trendPrediction: report.summary.trendPrediction,
    sentimentScore: report.summary.sentimentScore,
  };

  const details: ReportDetails = {
    belongBoards: (report.belongBoards || []).map((board) => ({
      name: board.name,
      type: board.type || '武器箱',
      code: board.code,
    })),
  };

  return (
    <div className="cs-dashboard animate-fade-in pb-6" data-product="cs">
      {onReanalyze ? (
        <div className="cs-dashboard-actions mb-4 flex flex-wrap items-center justify-end gap-2">
          <Button variant="home-action-ai" size="sm" disabled={isAnalyzing} onClick={onReanalyze}>
            重新分析
          </Button>
        </div>
      ) : null}

      <div className="cs-dashboard-zone cs-dashboard-zone-hero">
        <ReportOverview meta={meta} summary={summary} details={details} />
      </div>

      <div className="cs-dashboard-zone mt-4">
        <CsPlatformPrices data={data} />
      </div>

      <div className="cs-dashboard-zone mt-4">
        <ReportStrategy
          strategy={{
            idealBuy: report.strategy.idealBuy,
            secondaryBuy: report.strategy.secondaryBuy,
            stopLoss: report.strategy.stopLoss,
            takeProfit: report.strategy.takeProfit,
          }}
          language="zh"
        />
      </div>

      <div className="cs-dashboard-split mt-4 grid grid-cols-1 gap-4">
        <ReportDiagnostics summary={toRunDiagnosticSummary(report)} language="zh" />
        <CsReportNews items={data.eventIntel ?? []} containers={report.containers} />
      </div>

      <div className="cs-dashboard-zone mt-4">
        <CsTechnicalPanel data={data} defaultCollapsed />
      </div>

      <div className="cs-dashboard-zone mt-4">
        <CsReportMarkdown content={data.reportMarkdown} reportSource={data.reportSource} />
      </div>
    </div>
  );
};
