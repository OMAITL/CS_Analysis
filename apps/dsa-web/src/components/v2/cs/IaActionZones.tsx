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
  const buyRaw = strategy.idealBuy || strategy.secondaryBuy || '—';
  const buyParsed = parsePriceNumber(buyRaw);
  const buyDisplay =
    buyLow != null && buyHigh != null && buyLow !== buyHigh
      ? `${Math.min(buyLow, buyHigh).toFixed(0)} - ${Math.max(buyLow, buyHigh).toFixed(0)}`
      : buyParsed != null
        ? buyParsed.toFixed(0)
        : buyRaw;
  const buyUnit =
    buyLow != null && buyHigh != null && buyLow !== buyHigh ? '元' : buyParsed != null ? '元' : '';
  const buyHint =
    buyParsed != null && buyRaw.includes('元') && buyRaw.length > 8
      ? buyRaw
      : strategy.idealBuy
        ? '理想区间'
        : '参考均线';

  const zones = [
    {
      label: '推荐买入',
      value: buyDisplay,
      hint: buyHint,
      tone: 'buy' as const,
      unit: buyUnit,
    },
    {
      label: '止盈目标',
      value: take != null ? take.toFixed(0) : strategy.takeProfit || '—',
      hint: '到达阻力区可考虑止盈',
      tone: 'take' as const,
      unit: take != null ? '元' : '',
    },
    {
      label: '止损参考',
      value: stop != null ? stop.toFixed(0) : strategy.stopLoss || '—',
      hint: '跌破关键支撑止损',
      tone: 'stop' as const,
      unit: stop != null ? '元' : '',
    },
  ];

  return (
    <section className="ia-card ia-action-card">
      <h3 className="ia-section-title">操作参考</h3>
      <div className="ia-zone-grid">
        {zones.map((zone) => (
          <div key={zone.label} className={`ia-zone-card ia-zone-${zone.tone}`}>
            <p className="ia-zone-label">{zone.label}</p>
            <p className="ia-zone-value">
              {zone.value}
              {zone.unit ? <span className="ia-zone-unit">{zone.unit}</span> : null}
            </p>
            <p className="ia-zone-hint">{zone.hint}</p>
          </div>
        ))}
      </div>
    </section>
  );
};
