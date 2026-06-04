import type React from 'react';
import { useState } from 'react';
import { Card } from '../common';
import { DashboardPanelHeader } from '../dashboard';
import type { CsItemAnalyzeResponse } from '../../types/cs';

type CsTechnicalPanelProps = {
  data: CsItemAnalyzeResponse;
  defaultCollapsed?: boolean;
};

export const CsTechnicalPanel: React.FC<CsTechnicalPanelProps> = ({
  data,
  defaultCollapsed = true,
}) => {
  const [expanded, setExpanded] = useState(!defaultCollapsed);
  const { trend, meta } = data;
  const hasSignals = trend.signalReasons.length > 0 || trend.riskFactors.length > 0;

  if (!hasSignals) {
    return null;
  }

  return (
    <Card variant="bordered" padding="md" className="home-panel-card">
      <button
        type="button"
        onClick={() => setExpanded((open) => !open)}
        className="flex w-full items-center justify-between gap-2 text-left"
        aria-expanded={expanded}
      >
        <DashboardPanelHeader eyebrow="技术面" title="系统信号摘要" className="mb-0" />
        <span className="shrink-0 text-xs text-muted-text">{expanded ? '收起' : '展开'}</span>
      </button>
      {expanded ? (
        <>
          <div className="mb-4 mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div className="home-subpanel p-3 text-sm">
              <p className="text-xs text-muted-text">趋势</p>
              <p className="mt-1 font-medium text-foreground">{trend.trendStatus}</p>
            </div>
            <div className="home-subpanel p-3 text-sm">
              <p className="text-xs text-muted-text">MACD / RSI</p>
              <p className="mt-1 font-medium text-foreground">{trend.macdStatus} / {trend.rsiStatus}</p>
            </div>
            <div className="home-subpanel p-3 text-sm">
              <p className="text-xs text-muted-text">量比(5日)</p>
              <p className="mt-1 font-medium text-foreground">{trend.volumeRatio5d.toFixed(2)} · {trend.volumeStatus}</p>
            </div>
            <div className="home-subpanel p-3 text-sm">
              <p className="text-xs text-muted-text">数据质量</p>
              <p className="mt-1 font-medium text-foreground">{meta.dataQuality}</p>
            </div>
          </div>
          <div className="grid gap-4 lg:grid-cols-2">
            {trend.signalReasons.length > 0 ? (
              <div>
                <p className="label-uppercase mb-2 text-success">看多依据</p>
                <ul className="list-disc space-y-1 pl-5 text-sm text-secondary-text">
                  {trend.signalReasons.map((line) => (
                    <li key={line}>{line}</li>
                  ))}
                </ul>
              </div>
            ) : null}
            {trend.riskFactors.length > 0 ? (
              <div>
                <p className="label-uppercase mb-2 text-danger">风险因素</p>
                <ul className="list-disc space-y-1 pl-5 text-sm text-secondary-text">
                  {trend.riskFactors.map((line) => (
                    <li key={line}>{line}</li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>
        </>
      ) : null}
    </Card>
  );
};
