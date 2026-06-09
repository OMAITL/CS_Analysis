import type React from 'react';
import type { CsItemAnalyzeResponse } from '../../../types/cs';
import { buildReportFromData, humanizeTrendLine, splitTrendSignals } from './iaUtils';

type IaScoreBreakdownProps = {
  data: CsItemAnalyzeResponse;
};

export const IaScoreBreakdown: React.FC<IaScoreBreakdownProps> = ({ data }) => {
  const report = buildReportFromData(data);
  const score = report.summary.sentimentScore ?? data.trend.signalScore;
  const { bullish, bearish } = splitTrendSignals(
    data.trend.signalReasons ?? [],
    data.trend.riskFactors ?? [],
  );

  if (bullish.length === 0 && bearish.length === 0 && !report.summary.analysisSummary) {
    return null;
  }

  return (
    <section className="ia-card ia-score-card">
      <div className="ia-score-header">
        <div>
          <h3 className="ia-section-title ia-section-title-inline">评分依据</h3>
      {report.summary.analysisSummary ? (
        <p className="ia-section-lead">{humanizeTrendLine(report.summary.analysisSummary)}</p>
      ) : null}
        </div>
        <div className="ia-score-badge" aria-label={`综合得分 ${score} 分`}>
          <span className="ia-score-badge-value">{score}</span>
          <span className="ia-score-badge-label">综合得分</span>
        </div>
      </div>
      <div className="ia-score-meter" aria-hidden="true">
        <div className="ia-score-meter-fill" style={{ width: `${Math.max(0, Math.min(100, score))}%` }} />
      </div>
      <div className="ia-reason-grid">
        {bullish.length > 0 ? (
          <div className="ia-reason-col ia-reason-bull">
            <p className="ia-reason-label">利好因素</p>
            <ul>
              {bullish.map((line) => (
                <li key={line}>{humanizeTrendLine(line)}</li>
              ))}
            </ul>
          </div>
        ) : null}
        {bearish.length > 0 ? (
          <div className="ia-reason-col ia-reason-bear">
            <p className="ia-reason-label">利空因素</p>
            <ul>
              {bearish.map((line) => (
                <li key={line}>{humanizeTrendLine(line)}</li>
              ))}
            </ul>
          </div>
        ) : null}
      </div>
    </section>
  );
};
