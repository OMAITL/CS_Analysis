import type React from 'react';
import type { CsItemAnalyzeResponse } from '../../../types/cs';
import { buildReportFromData } from './iaUtils';

type IaScoreBreakdownProps = {
  data: CsItemAnalyzeResponse;
};

export const IaScoreBreakdown: React.FC<IaScoreBreakdownProps> = ({ data }) => {
  const report = buildReportFromData(data);
  const score = report.summary.sentimentScore ?? data.trend.signalScore;
  const bullish = data.trend.signalReasons ?? [];
  const bearish = data.trend.riskFactors ?? [];

  if (bullish.length === 0 && bearish.length === 0 && !report.summary.analysisSummary) {
    return null;
  }

  return (
    <section className="ia-card">
      <h3 className="ia-section-title">评分依据</h3>
      {report.summary.analysisSummary ? (
        <p className="ia-section-lead">{report.summary.analysisSummary}</p>
      ) : null}
      <div className="ia-reason-grid">
        {bullish.length > 0 ? (
          <div className="ia-reason-col ia-reason-bull">
            <p className="ia-reason-label">利好因素</p>
            <ul>
              {bullish.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          </div>
        ) : null}
        {bearish.length > 0 ? (
          <div className="ia-reason-col ia-reason-bear">
            <p className="ia-reason-label">利空因素</p>
            <ul>
              {bearish.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          </div>
        ) : null}
      </div>
      <div className="ia-score-final">
        <span>综合得分</span>
        <strong>{score} / 100</strong>
      </div>
    </section>
  );
};
