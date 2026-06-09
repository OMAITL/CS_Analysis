import type React from 'react';
import { buildReportFromData } from './iaUtils';

type IaSentimentBarProps = {
  score: number;
};

export const IaSentimentBar: React.FC<IaSentimentBarProps> = ({ score }) => {
  const clamped = Math.max(0, Math.min(100, score));
  const label =
    clamped >= 65 ? '偏乐观' : clamped >= 40 ? '中性' : '偏悲观';

  return (
    <div className="ia-sentiment-bar-wrap">
      <div className="ia-sentiment-labels">
        <span>极度悲观</span>
        <span>极度乐观</span>
      </div>
      <div className="ia-sentiment-track" aria-hidden="true">
        <div className="ia-sentiment-fill" style={{ width: `${clamped}%` }} />
        <div className="ia-sentiment-thumb" style={{ left: `${clamped}%` }} />
      </div>
      <div className="ia-sentiment-foot">
        <strong>{clamped}</strong>
        <span className="ia-muted">{label}</span>
      </div>
    </div>
  );
};

export const IaSentimentSection: React.FC<{ data: import('../../../types/cs').CsItemAnalyzeResponse }> = ({
  data,
}) => {
  const report = buildReportFromData(data);
  const score = report.summary.sentimentScore ?? data.trend.signalScore;
  return (
    <section className="ia-card ia-card-compact ia-sentiment-card">
      <div className="ia-sentiment-head">
        <h3 className="ia-section-title ia-section-title-inline">市场情绪</h3>
        <div className="ia-sentiment-score-pill">
          <strong>{Math.max(0, Math.min(100, score))}</strong>
          <span className="ia-muted">/ 100</span>
        </div>
      </div>
      <IaSentimentBar score={score} />
    </section>
  );
};
