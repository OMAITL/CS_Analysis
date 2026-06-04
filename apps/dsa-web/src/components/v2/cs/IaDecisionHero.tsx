import type React from 'react';
import type { CsItemAnalyzeResponse } from '../../../types/cs';
import {
  buildReportFromData,
  humanizeAdvice,
  resolveAdviceTone,
  resolveRiskLevel,
  type AdviceTone,
} from './iaUtils';

type IaDecisionHeroProps = {
  data: CsItemAnalyzeResponse;
};

const toneClass: Record<AdviceTone, string> = {
  bullish: 'ia-tone-bullish',
  bearish: 'ia-tone-bearish',
  neutral: 'ia-tone-neutral',
};

export const IaDecisionHero: React.FC<IaDecisionHeroProps> = ({ data }) => {
  const report = buildReportFromData(data);
  const lastBar = data.ohlcv[data.ohlcv.length - 1];
  const price = data.trend.currentPrice || lastBar?.close;
  const changePct = lastBar?.changePercent;
  const score = report.summary.sentimentScore ?? data.trend.signalScore;
  const advice = humanizeAdvice(report.summary.operationAdvice || data.trend.buySignal);
  const tone = resolveAdviceTone(report.summary.operationAdvice || data.trend.buySignal);
  const risk = resolveRiskLevel(score);
  const trend = report.summary.trendPrediction || data.trend.trendStatus;

  const changeText =
    changePct == null || !Number.isFinite(changePct)
      ? null
      : `${changePct > 0 ? '+' : ''}${changePct.toFixed(2)}%`;

  return (
    <section className="ia-card ia-decision-hero">
      <div className="ia-decision-head">
        <div>
          <h2 className="ia-decision-title">{data.itemName}</h2>
          <div className="ia-decision-price-row">
            {price != null && Number.isFinite(price) ? (
              <span className="ia-decision-price">{Number(price).toFixed(2)}</span>
            ) : null}
            {changeText ? (
              <span className={changePct && changePct >= 0 ? 'ia-price-up' : 'ia-price-down'}>
                {changeText}
              </span>
            ) : null}
            <span className="ia-muted text-xs">{data.platform.toUpperCase()} 参考价</span>
          </div>
        </div>
        <div className="ia-score-ring">
          <span className="ia-score-value">{score}</span>
          <span className="ia-score-label">AI 评分</span>
        </div>
      </div>

      <div className="ia-decision-grid">
        <div className={`ia-decision-block ${toneClass[tone]}`}>
          <p className="ia-block-label">当前建议</p>
          <p className="ia-block-value">{advice}</p>
        </div>
        <div className={`ia-decision-block ${toneClass[risk.tone]}`}>
          <p className="ia-block-label">风险等级</p>
          <p className="ia-block-value">{risk.label}</p>
        </div>
        <div className="ia-decision-block">
          <p className="ia-block-label">趋势判断</p>
          <p className="ia-block-value">{trend}</p>
        </div>
      </div>
    </section>
  );
};
