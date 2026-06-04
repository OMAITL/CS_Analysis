import type React from 'react';
import { Card } from '../common';
import type { CsEventIntelItem } from '../../types/cs';

const DIMENSION_LABELS: Record<string, string> = {
  item_focus: '本品聚焦',
  case_focus: '所属武器箱',
  official_crawl: '官方博客（RSS）',
  hltv_crawl: 'HLTV（爬虫）',
  official_update: '官方更新（搜索）',
  new_case: '新箱子',
  cs_market: '饰品市场',
  major_sticker: 'Major/贴纸',
  hltv: 'HLTV（搜索）',
  tieba: '贴吧',
};

const RELEVANCE_LABELS: Record<string, string> = {
  direct: '本品相关',
  case: '武器箱相关',
  market: '市场要闻',
};

const RELEVANCE_ORDER = ['direct', 'case', 'market'] as const;

type CsEventIntelPanelProps = {
  items: CsEventIntelItem[];
};

function groupByRelevance(items: CsEventIntelItem[]): { tier: string; rows: CsEventIntelItem[] }[] {
  const groups: { tier: string; rows: CsEventIntelItem[] }[] = [];
  for (const tier of RELEVANCE_ORDER) {
    const rows = items.filter((i) => i.relevance === tier);
    if (rows.length) {
      groups.push({ tier, rows });
    }
  }
  const other = items.filter(
    (i) => !RELEVANCE_ORDER.includes(i.relevance as (typeof RELEVANCE_ORDER)[number]),
  );
  if (other.length) {
    groups.push({ tier: 'market', rows: other });
  }
  return groups;
}

export const CsEventIntelPanel: React.FC<CsEventIntelPanelProps> = ({ items }) => {
  if (!items.length) {
    return (
      <Card variant="bordered" padding="md">
        <h3 className="mb-2 text-sm font-semibold text-foreground">事件与舆论</h3>
        <p className="text-sm text-secondary-text">
          本次分析未检索到明显相关的事件条目，这属于正常情况：多数新闻不会点名具体皮肤。若饰品有所属武器箱，系统会额外搜索武器箱相关资讯；仍无结果时可稍后重试或调整搜索配置。
        </p>
      </Card>
    );
  }

  const grouped = groupByRelevance(items);

  return (
    <Card variant="bordered" padding="md">
      <h3 className="mb-3 text-sm font-semibold text-foreground">事件与舆论（分析时快照）</h3>
      <p className="mb-4 text-xs text-secondary-text">
        未出现「本品相关」条目也属正常；武器箱相关新闻可能间接影响同箱饰品价格。
      </p>
      <div className="space-y-5">
        {grouped.map(({ tier, rows }) => (
          <section key={tier}>
            <h4 className="mb-2 text-xs font-medium uppercase tracking-wide text-secondary-text">
              {RELEVANCE_LABELS[tier] ?? tier}
            </h4>
            <ul className="space-y-3">
              {rows.map((item) => {
                const dimLabel = DIMENSION_LABELS[item.dimension ?? ''] ?? item.dimension;
                const key = `${item.dimension}-${item.url || item.title}`;
                return (
                  <li key={key} className="border-b border-border/40 pb-3 last:border-0 last:pb-0">
                    <div className="mb-1 flex flex-wrap items-center gap-2">
                      <span className="rounded-md bg-muted px-2 py-0.5 text-xs text-secondary-text">
                        {dimLabel}
                      </span>
                      {item.source ? (
                        <span className="text-xs text-secondary-text">{item.source}</span>
                      ) : null}
                    </div>
                    {item.url ? (
                      <a
                        href={item.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm font-medium text-primary hover:underline"
                      >
                        {item.title}
                      </a>
                    ) : (
                      <p className="text-sm font-medium text-foreground">{item.title}</p>
                    )}
                    {item.snippet ? (
                      <p className="mt-1 line-clamp-2 text-xs text-secondary-text">{item.snippet}</p>
                    ) : null}
                  </li>
                );
              })}
            </ul>
          </section>
        ))}
      </div>
    </Card>
  );
};
