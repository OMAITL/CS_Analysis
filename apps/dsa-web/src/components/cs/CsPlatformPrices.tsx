import type React from 'react';
import type { CsItemAnalyzeResponse } from '../../types/cs';
import { Badge, Card } from '../common';

type CsPlatformPricesProps = {
  data: CsItemAnalyzeResponse;
};

export const CsPlatformPrices: React.FC<CsPlatformPricesProps> = ({ data }) => {
  const { snapshot, meta, platform } = data;
  const hasPrices =
    snapshot.buffSellPrice != null
    || snapshot.yyypSellPrice != null
    || snapshot.steamSellPrice != null
    || snapshot.yyypSellNum != null
    || snapshot.buffSellNum != null;

  if (!hasPrices) {
    return null;
  }

  return (
    <Card variant="bordered" padding="sm" className="home-panel-card text-left">
      <section aria-label="平台价格与流动性">
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <span className="label-uppercase">平台价格</span>
          <Badge variant={meta.dataQuality === 'full' ? 'success' : 'warning'}>
            {meta.dataQuality}
          </Badge>
          <span className="home-accent-chip px-2 py-0.5 text-xs">{platform.toUpperCase()}</span>
        </div>
        <div className="flex flex-wrap gap-2 text-sm">
          {snapshot.buffSellPrice != null ? (
            <span className="home-accent-chip px-2 py-0.5 text-xs">BUFF {snapshot.buffSellPrice}</span>
          ) : null}
          {snapshot.yyypSellPrice != null ? (
            <span className="home-accent-chip px-2 py-0.5 text-xs">YYYP {snapshot.yyypSellPrice}</span>
          ) : null}
          {snapshot.steamSellPrice != null ? (
            <span className="home-accent-chip px-2 py-0.5 text-xs">Steam {snapshot.steamSellPrice}</span>
          ) : null}
          {snapshot.yyypSellNum != null ? (
            <span className="home-board-pill rounded-full px-2 py-0.5 text-xs">
              YYYP 挂牌 {snapshot.yyypSellNum}
            </span>
          ) : null}
          {snapshot.buffSellNum != null ? (
            <span className="home-board-pill rounded-full px-2 py-0.5 text-xs">
              BUFF 挂牌 {snapshot.buffSellNum}
            </span>
          ) : null}
        </div>
      </section>
    </Card>
  );
};
