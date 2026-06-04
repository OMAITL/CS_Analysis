import type React from 'react';
import { Card } from '../common';
import { DashboardPanelHeader, DashboardStateBlock } from '../dashboard';
import type { CsEventIntelItem, CsItemContainer } from '../../types/cs';

type CsReportNewsProps = {
  items: CsEventIntelItem[];
  containers?: CsItemContainer[];
};

const DIMENSION_LABELS: Record<string, string> = {
  item_focus: '本品相关',
  case_focus: '武器箱相关',
  official_crawl: '官方动态',
  hltv_crawl: 'HLTV',
  official_update: '官方更新',
  new_case: '新箱子',
  cs_market: '市场要闻',
  hltv: 'HLTV',
  major_sticker: 'Major/贴纸',
  tieba: '社区',
};

export const CsReportNews: React.FC<CsReportNewsProps> = ({ items, containers = [] }) => {
  return (
    <Card variant="bordered" padding="md" className="home-panel-card">
      <DashboardPanelHeader eyebrow="资讯动态" title="事件与舆论" className="mb-3" />

      {containers.length > 0 ? (
        <div className="mb-4">
          <p className="label-uppercase mb-2">所属武器箱</p>
          <div className="flex flex-wrap gap-2">
            {containers.map((container) => (
              <span key={`${container.name}-${container.goodId ?? 'na'}`} className="home-accent-chip px-2 py-0.5 text-xs">
                {container.name}
                {container.price != null ? ` · ${container.price}` : ''}
              </span>
            ))}
          </div>
        </div>
      ) : null}

      {items.length === 0 ? (
        <DashboardStateBlock
          compact
          title="暂无相关资讯"
          description="未检索到高相关事件；武器箱/市场类间接影响仍可能存在。"
        />
      ) : (
        <div className="space-y-3 text-left">
          {items.map((item, index) => (
            <div key={`${item.title}-${index}`} className="home-subpanel home-news-item group p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="mb-1 flex flex-wrap items-center gap-2">
                    {item.dimension ? (
                      <span className="home-board-pill rounded-full px-2 py-0.5 text-[10px]">
                        {DIMENSION_LABELS[item.dimension] || item.dimension}
                      </span>
                    ) : null}
                    {item.source ? (
                      <span className="text-[10px] text-muted-text">{item.source}</span>
                    ) : null}
                  </div>
                  <p className="home-news-title text-sm font-medium leading-6 text-foreground">
                    {item.title}
                  </p>
                  {item.snippet ? (
                    <p className="home-news-snippet mt-2 text-sm leading-6 text-secondary-text overflow-hidden [display:-webkit-box] [-webkit-line-clamp:3] [-webkit-box-orient:vertical]">
                      {item.snippet}
                    </p>
                  ) : null}
                </div>
                {item.url ? (
                  <a
                    href={item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="home-accent-pill-link shrink-0 whitespace-nowrap px-2.5 py-1 text-xs"
                  >
                    打开链接
                  </a>
                ) : null}
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
};
