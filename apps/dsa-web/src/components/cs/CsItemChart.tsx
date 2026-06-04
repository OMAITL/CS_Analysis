import type React from 'react';
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { CsKlineBar } from '../../types/cs';

type CsItemChartProps = {
  data: CsKlineBar[];
};

export const CsItemChart: React.FC<CsItemChartProps> = ({ data }) => {
  if (!data.length) {
    return (
      <div className="flex h-72 items-center justify-center text-sm text-secondary-text">
        暂无 K 线数据
      </div>
    );
  }

  // Use full ISO date as the X key — MM-DD alone collides across years (755 bars → ~365 labels).
  const chartData = data.map((row) => ({
    date: row.date,
    close: row.close,
    volume: row.volume ?? 0,
  }));

  const formatAxisDate = (value: string) => {
    if (value.length >= 10) {
      return value.slice(5);
    }
    return value;
  };

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={chartData} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11 }}
            tickFormatter={formatAxisDate}
            minTickGap={24}
          />
          <YAxis
            yAxisId="price"
            tick={{ fontSize: 11 }}
            domain={['auto', 'auto']}
            width={56}
          />
          <YAxis yAxisId="volume" orientation="right" tick={{ fontSize: 11 }} width={48} />
          <Tooltip
            labelFormatter={(value) => String(value)}
            contentStyle={{
              background: 'hsl(var(--card))',
              border: '1px solid hsl(var(--border))',
              borderRadius: 12,
            }}
          />
          <Legend />
          <Bar yAxisId="volume" dataKey="volume" name="成交量" fill="hsl(var(--primary) / 0.35)" />
          <Line
            yAxisId="price"
            type="monotone"
            dataKey="close"
            name="收盘价"
            stroke="hsl(var(--primary))"
            strokeWidth={2}
            dot={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
      <p className="mt-2 text-xs text-muted-text">
        成交量为 K 线真实成交笔数（非挂牌量）。旧数据缺 OHLC 时收盘价可能为 flat bar。
      </p>
    </div>
  );
};
