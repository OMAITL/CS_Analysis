import type React from 'react';
import { Badge, Card } from '../common';
import type { CsItemAnalyzeResponse } from '../../types/cs';

type CsTrendSummaryProps = {
  data: CsItemAnalyzeResponse;
};

function fmtNum(value: unknown, digits = 2): string {
  const n = typeof value === 'number' ? value : Number(value);
  return Number.isFinite(n) ? n.toFixed(digits) : '—';
}

export const CsTrendSummary: React.FC<CsTrendSummaryProps> = ({ data }) => {
  const { trend, meta, snapshot } = data;

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card variant="gradient" padding="md">
        <p className="label-uppercase mb-3">技术面</p>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between gap-3">
            <span className="text-secondary-text">趋势</span>
            <span className="font-medium text-foreground">{trend.trendStatus}</span>
          </div>
          <div className="flex justify-between gap-3">
            <span className="text-secondary-text">信号</span>
            <Badge variant="warning">{trend.buySignal}</Badge>
          </div>
          <div className="flex justify-between gap-3">
            <span className="text-secondary-text">评分</span>
            <span className="font-medium text-foreground">{trend.signalScore}/100</span>
          </div>
          <div className="flex justify-between gap-3">
            <span className="text-secondary-text">现价</span>
            <span className="font-medium text-foreground">{fmtNum(trend.currentPrice)}</span>
          </div>
          <div className="flex justify-between gap-3">
            <span className="text-secondary-text">量比(5日)</span>
            <span className="font-medium text-foreground">{fmtNum(trend.volumeRatio5d)}</span>
          </div>
          <div className="flex justify-between gap-3">
            <span className="text-secondary-text">量能</span>
            <span className="font-medium text-foreground">{trend.volumeStatus}</span>
          </div>
          <div className="flex justify-between gap-3">
            <span className="text-secondary-text">RSI / MACD</span>
            <span className="font-medium text-foreground">
              {trend.rsiStatus} / {trend.macdStatus}
            </span>
          </div>
        </div>
      </Card>

      <Card padding="md">
        <p className="label-uppercase mb-3">数据与平台</p>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between gap-3">
            <span className="text-secondary-text">数据质量</span>
            <Badge variant={meta.dataQuality === 'full' ? 'success' : 'warning'}>
              {meta.dataQuality}
            </Badge>
          </div>
          <div className="flex justify-between gap-3">
            <span className="text-secondary-text">OHLC 来源</span>
            <span className="text-foreground">{meta.ohlcSource}</span>
          </div>
          <div className="flex justify-between gap-3">
            <span className="text-secondary-text">成交量来源</span>
            <span className="text-foreground">{meta.volumeSource}</span>
          </div>
          <div className="flex justify-between gap-3">
            <span className="text-secondary-text">K 线条数</span>
            <span className="text-foreground">{meta.rowCount}</span>
          </div>
          {snapshot.buffSellPrice != null ? (
            <div className="flex justify-between gap-3">
              <span className="text-secondary-text">BUFF</span>
              <span className="text-foreground">{snapshot.buffSellPrice}</span>
            </div>
          ) : null}
          {snapshot.yyypSellPrice != null ? (
            <div className="flex justify-between gap-3">
              <span className="text-secondary-text">悠悠有品</span>
              <span className="text-foreground">{snapshot.yyypSellPrice}</span>
            </div>
          ) : null}
          {snapshot.yyypSellNum != null ? (
            <div className="flex justify-between gap-3">
              <span className="text-secondary-text">YYYP 挂牌</span>
              <span className="text-foreground">{snapshot.yyypSellNum}</span>
            </div>
          ) : null}
        </div>
      </Card>
    </div>
  );
};
