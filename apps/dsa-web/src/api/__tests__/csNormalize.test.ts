import { describe, expect, it } from 'vitest';

import { normalizeCsTrend } from '../csNormalize';

describe('normalizeCsTrend', () => {
  it('maps volumeRatio5D from camelcase-keys to volumeRatio5d', () => {
    const trend = normalizeCsTrend({
      code: 'test',
      trendStatus: '震荡',
      volumeRatio5D: 1.25,
      currentPrice: 947.37,
    });

    expect(trend.volumeRatio5d).toBe(1.25);
    expect(trend.currentPrice).toBe(947.37);
  });
});
