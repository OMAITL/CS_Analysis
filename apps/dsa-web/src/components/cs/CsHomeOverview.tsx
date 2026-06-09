import type React from 'react';
import type { CsItemAnalyzeResponse } from '../../types/cs';
import { Badge, Card, ScoreGauge } from '../common';

type CsHomeOverviewProps = {
  data: CsItemAnalyzeResponse;
};

function formatChangePct(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) {
    return '--';
  }
  const sign = value > 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

function extractCoreInsight(markdown: string, fallback: string): string {
  const text = markdown.trim();
  if (!text) {
    return fallback;
  }
  const match = text.match(/##\s*核心结论\s*\n+([\s\S]*?)(?=\n##\s|\n#|$)/i);
  if (match?.[1]) {
    const section = match[1].trim().replace(/\n+/g, ' ').slice(0, 320);
    if (section) {
      return section;
    }
  }
  const firstParagraph = text.split(/\n\n+/).find((block) => block.trim() && !block.startsWith('#'));
  return (firstParagraph || fallback).trim().slice(0, 320);
}

export const CsHomeOverview: React.FC<CsHomeOverviewProps> = ({ data }) => {
  const { trend, meta, snapshot, reportMarkdown } = data;
  const lastBar = data.ohlcv[data.ohlcv.length - 1];
  const changePct = lastBar?.changePercent ?? null;
  const price = trend.currentPrice || lastBar?.close || snapshot.yyypSellPrice || snapshot.buffSellPrice;

  const insightFallback = trend.signalReasons.slice(0, 2).join('；') || '暂无技术面摘要';
  const insight = extractCoreInsight(reportMarkdown, insightFallback);

  const priceStyle: React.CSSProperties | undefined = changePct == null
    ? undefined
    : changePct > 0
      ? { color: 'var(--home-price-up)' }
      : changePct < 0
        ? { color: 'var(--home-price-down)' }
        : undefined;

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-1 items-start gap-5 lg:grid-cols-3">
        <div className="space-y-5 lg:col-span-2">
          <Card variant="gradient" padding="md" className="home-report-hero">
            <div className="mb-5 flex items-start justify-between">
              <div className="flex-1">
                <div className="flex flex-wrap items-center gap-3">
                  <h2 className="text-[28px] font-bold leading-tight text-foreground">
                    {data.itemName}
                  </h2>
                  {price != null && Number.isFinite(price) ? (
                    <div className="flex items-baseline gap-2">
                      <span className="font-mono text-xl font-bold" style={priceStyle}>
                        {Number(price).toFixed(2)}
                      </span>
                      <span className="font-mono text-sm font-semibold" style={priceStyle}>
                        {formatChangePct(changePct)}
                      </span>
                    </div>
                  ) : null}
                </div>
                <div className="mt-1.5 flex flex-wrap items-center gap-2">
                  <span className="home-accent-chip px-2 py-0.5 text-xs">
                    {data.platform.toUpperCase()}
                  </span>
                  <Badge variant={meta.dataQuality === 'full' ? 'success' : 'warning'}>
                    {meta.dataQuality}
                  </Badge>
                </div>
              </div>
            </div>
            <div className="home-divider border-t pt-5">
              <span className="label-uppercase">核心洞察</span>
              <p className="mt-2 max-w-[62ch] whitespace-pre-wrap text-left text-[15px] leading-7 text-foreground">
                {insight}
              </p>
            </div>
          </Card>

          <div className="grid grid-cols-1 items-start gap-4 md:grid-cols-2">
            <Card
              variant="bordered"
              padding="sm"
              hoverable
              className="home-panel-card home-insight-card"
              style={{ ['--home-insight-tone' as string]: 'var(--home-strategy-buy)' }}
            >
              <div className="flex items-start gap-3">
                <div className="home-insight-icon flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-success/10">
                  <svg className="h-4 w-4 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                  </svg>
                </div>
                <div className="space-y-1.5">
                  <h4 className="home-insight-title text-[11px] font-medium uppercase tracking-[0.16em]">操作建议</h4>
                  <p className="home-insight-body text-sm leading-6">{trend.buySignal || '观望'}</p>
                </div>
              </div>
            </Card>

            <Card variant="bordered" padding="sm" className="home-panel-card text-left">
              <section aria-label="平台与流动性">
                <div className="mb-3 flex items-baseline gap-2">
                  <span className="label-uppercase">平台价格</span>
                </div>
                <div className="flex flex-wrap gap-2 text-sm">
                  {snapshot.buffSellPrice != null ? (
                    <span className="home-accent-chip px-2 py-0.5 text-xs">BUFF {snapshot.buffSellPrice}</span>
                  ) : null}
                  {snapshot.yyypSellPrice != null ? (
                    <span className="home-accent-chip px-2 py-0.5 text-xs">YYYP {snapshot.yyypSellPrice}</span>
                  ) : null}
                  {snapshot.yyypSellNum != null ? (
                    <span className="home-board-pill rounded-full px-2 py-0.5 text-xs">
                      挂牌 {snapshot.yyypSellNum}
                    </span>
                  ) : null}
                </div>
              </section>
            </Card>

            <Card
              variant="bordered"
              padding="sm"
              hoverable
              className="home-panel-card home-insight-card md:col-span-2"
              style={{ ['--home-insight-tone' as string]: 'var(--home-strategy-take)' }}
            >
              <div className="flex items-start gap-3">
                <div className="home-insight-icon flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-warning/10">
                  <svg className="h-4 w-4 text-warning" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                  </svg>
                </div>
                <div className="space-y-1.5">
                  <h4 className="home-insight-title text-[11px] font-medium uppercase tracking-[0.16em]">趋势判断</h4>
                  <p className="home-insight-body text-sm leading-6">
                    {trend.trendStatus}
                    {trend.maAlignment ? ` · ${trend.maAlignment}` : ''}
                  </p>
                </div>
              </div>
            </Card>
          </div>
        </div>

        <div className="flex flex-col">
          <Card variant="bordered" padding="md" className="home-panel-card home-rail-card !overflow-visible">
            <div className="text-center">
              <h3 className="mb-5 text-sm font-medium tracking-wide text-foreground">信号评分</h3>
              <ScoreGauge score={trend.signalScore} size="lg" language="zh" />
              <p className="mt-3 text-xs text-muted-text">
                {trend.volumeStatus} · 量比 {trend.volumeRatio5d.toFixed(2)}
              </p>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
