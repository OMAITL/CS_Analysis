import type React from 'react';
import { useState } from 'react';
import type { CsEventIntelItem } from '../../../types/cs';
import { ChevronDown } from 'lucide-react';

function guessImpact(item: CsEventIntelItem): { label: string; tone: 'bullish' | 'bearish' | 'neutral' } {
  const text = `${item.title} ${item.snippet ?? ''}`.toLowerCase();
  const bearishHints = ['跌', '降', '利空', '减持', '风险', '跌', 'drop', 'fall'];
  const bullishHints = ['涨', '升', '利多', '利好', 'major', '开赛', 'hot', 'rise'];
  if (bearishHints.some((h) => text.includes(h))) {
    return { label: '利空', tone: 'bearish' };
  }
  if (bullishHints.some((h) => text.includes(h))) {
    return { label: '利多', tone: 'bullish' };
  }
  return { label: '中性', tone: 'neutral' };
}

type IaNewsBriefsProps = {
  items: CsEventIntelItem[];
};

export const IaNewsBriefs: React.FC<IaNewsBriefsProps> = ({ items }) => {
  const [expanded, setExpanded] = useState<Record<number, boolean>>({});

  if (items.length === 0) {
    return (
      <section className="ia-card">
        <h3 className="ia-section-title">市场资讯</h3>
        <p className="ia-muted text-sm">暂无高相关资讯，可稍后重新分析获取更新。</p>
      </section>
    );
  }

  return (
    <section className="ia-card">
      <h3 className="ia-section-title">市场资讯</h3>
      <ul className="ia-news-list">
        {items.map((item, index) => {
          const impact = guessImpact(item);
          const isOpen = expanded[index];
          return (
            <li key={`${item.title}-${index}`} className="ia-news-item">
              <button
                type="button"
                className="ia-news-head"
                onClick={() => setExpanded((prev) => ({ ...prev, [index]: !prev[index] }))}
                aria-expanded={isOpen}
              >
                <div className="ia-news-head-main">
                  <p className="ia-news-title">{item.title}</p>
                  <div className="ia-news-tags">
                    <span className={`ia-impact-pill ia-impact-${impact.tone}`}>
                      影响：{impact.label}
                    </span>
                    {item.source ? <span className="ia-muted text-xs">{item.source}</span> : null}
                  </div>
                </div>
                <ChevronDown className={`h-4 w-4 shrink-0 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
              </button>
              {isOpen && item.snippet ? (
                <div className="ia-news-body">
                  <p>{item.snippet}</p>
                  {item.url ? (
                    <a href={item.url} target="_blank" rel="noopener noreferrer" className="ia-link">
                      查看原文
                    </a>
                  ) : null}
                </div>
              ) : null}
            </li>
          );
        })}
      </ul>
    </section>
  );
};
