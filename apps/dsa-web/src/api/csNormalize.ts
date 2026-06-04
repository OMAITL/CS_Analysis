import type { CsItemAnalyzeResponse, CsItemTrend, CsReportPayload } from '../types/cs';

/** camelcase-keys turns `volume_ratio_5d` into `volumeRatio5D`, not `volumeRatio5d`. */
type RawCsItemTrend = Partial<CsItemTrend> & { volumeRatio5D?: number };

export function normalizeCsTrend(trend: RawCsItemTrend): CsItemTrend {
  return {
    code: trend.code ?? '',
    trendStatus: trend.trendStatus ?? '',
    maAlignment: trend.maAlignment ?? '',
    currentPrice: trend.currentPrice ?? 0,
    ma5: trend.ma5 ?? 0,
    ma10: trend.ma10 ?? 0,
    ma20: trend.ma20 ?? 0,
    ma60: trend.ma60 ?? 0,
    biasMa5: trend.biasMa5 ?? 0,
    volumeStatus: trend.volumeStatus ?? '',
    volumeRatio5d: trend.volumeRatio5d ?? trend.volumeRatio5D ?? 0,
    buySignal: trend.buySignal ?? '',
    signalScore: trend.signalScore ?? 0,
    signalReasons: trend.signalReasons ?? [],
    riskFactors: trend.riskFactors ?? [],
    macdStatus: trend.macdStatus ?? '',
    rsiStatus: trend.rsiStatus ?? '',
    macdDif: trend.macdDif ?? 0,
    macdDea: trend.macdDea ?? 0,
    rsi12: trend.rsi12 ?? 0,
  };
}

export function normalizeCsAnalyzeResponse(data: CsItemAnalyzeResponse): CsItemAnalyzeResponse {
  const report = data.report;
  const normalizedReport: CsReportPayload | undefined = report
    ? {
        summary: {
          analysisSummary: report.summary?.analysisSummary ?? '',
          operationAdvice: report.summary?.operationAdvice ?? '',
          trendPrediction: report.summary?.trendPrediction ?? '',
          sentimentScore: report.summary?.sentimentScore ?? 0,
        },
        strategy: {
          idealBuy: report.strategy?.idealBuy,
          secondaryBuy: report.strategy?.secondaryBuy,
          stopLoss: report.strategy?.stopLoss,
          takeProfit: report.strategy?.takeProfit,
        },
        diagnostics: {
          status: report.diagnostics?.status,
          statusLabel: report.diagnostics?.statusLabel,
          reason: report.diagnostics?.reason,
          components: report.diagnostics?.components ?? {},
          copyText: report.diagnostics?.copyText,
        },
        containers: report.containers ?? [],
        belongBoards: report.belongBoards ?? [],
      }
    : undefined;

  return {
    ...data,
    trend: normalizeCsTrend(data.trend ?? {}),
    report: normalizedReport,
  };
}
