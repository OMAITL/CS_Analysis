import type React from 'react';
import type { CsItemAnalyzeResponse } from '../../../types/cs';
import { calcSpreadPct } from './iaUtils';

type PriceRow = {
  key: string;
  label: string;
  price: number | null;
};

export const IaPlatformArbitrage: React.FC<{ data: CsItemAnalyzeResponse }> = ({ data }) => {
  const { snapshot } = data;
  const rows: PriceRow[] = [
    { key: 'buff', label: 'BUFF', price: snapshot.buffSellPrice ?? null },
    { key: 'yyyp', label: '悠悠有品', price: snapshot.yyypSellPrice ?? null },
    { key: 'steam', label: 'Steam', price: snapshot.steamSellPrice ?? null },
  ].filter((row) => row.price != null) as PriceRow[];

  if (rows.length < 2) {
    return null;
  }

  const sorted = [...rows].sort((a, b) => (a.price ?? 0) - (b.price ?? 0));
  const low = sorted[0];
  const high = sorted[sorted.length - 1];
  const spread = calcSpreadPct(low.price ?? 0, high.price ?? 0);
  const hasArb = spread != null && spread > 8;

  return (
    <section className="ia-card">
      <h3 className="ia-section-title">平台价格对比</h3>
      <div className="ia-platform-grid">
        {rows.map((row) => (
          <div key={row.key} className="ia-platform-item">
            <span className="ia-platform-label">{row.label}</span>
            <span className="ia-platform-price">{row.price?.toFixed(0)}</span>
          </div>
        ))}
      </div>
      {spread != null ? (
        <div className={`ia-arb-banner ${hasArb ? 'ia-arb-banner-hot' : ''}`}>
          <p>
            <span className="ia-muted">最低价 {low.label}</span> → <span className="ia-muted">最高价 {high.label}</span>
          </p>
          <p className="ia-arb-spread">
            价差 <strong>{spread > 0 ? '+' : ''}{spread.toFixed(1)}%</strong>
            {hasArb ? ' · 存在套利空间（需扣除手续费）' : ' · 价差正常'}
          </p>
        </div>
      ) : null}
    </section>
  );
};
