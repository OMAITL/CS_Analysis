import type React from 'react';
import type { CsItemAnalyzeResponse } from '../../../types/cs';
import { buildReportFromData, parsePriceNumber } from './iaUtils';

export const IaActionZones: React.FC<{ data: CsItemAnalyzeResponse }> = ({ data }) => {
  const report = buildReportFromData(data);
  const { strategy } = report;
  const ideal = parsePriceNumber(strategy.idealBuy);
  const secondary = parsePriceNumber(strategy.secondaryBuy);
  const stop = parsePriceNumber(strategy.stopLoss);
  const take = parsePriceNumber(strategy.takeProfit);

  const buyLow = ideal ?? secondary;
  const buyHigh = secondary && ideal ? Math.max(ideal, secondary) : (ideal ?? secondary);

  const zones = [
    {
      label: '推荐买入',
      value:
        buyLow != null && buyHigh != null && buyLow !== buyHigh
          ? `${Math.min(buyLow, buyHigh).toFixed(0)} - ${Math.max(buyLow, buyHigh).toFixed(0)}`
          : strategy.idealBuy || strategy.secondaryBuy || '—',
      hint: strategy.idealBuy ? '理想区间' : '参考均线',
      tone: 'buy',
    },
    {
      label: '止盈目标',
      value: take != null ? take.toFixed(0) : strategy.takeProfit || '—',
      hint: '到达阻力区可考虑止盈',
      tone: 'take',
    },
    {
      label: '止损参考',
      value: stop != null ? stop.toFixed(0) : strategy.stopLoss || '—',
      hint: '跌破关键支撑止损',
      tone: 'stop',
    },
  ];

  return (
    <section className="ia-card">
      <h3 className="ia-section-title">操作参考</h3>
      <div className="ia-zone-grid">
        {zones.map((zone) => (
          <div key={zone.label} className={`ia-zone-card ia-zone-${zone.tone}`}>
            <p className="ia-zone-label">{zone.label}</p>
            <p className="ia-zone-value">{zone.value}</p>
            <p className="ia-zone-hint">{zone.hint}</p>
          </div>
        ))}
      </div>
    </section>
  );
};
