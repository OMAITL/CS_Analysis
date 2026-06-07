import type React from 'react';
import { History, PanelLeftClose, PanelLeftOpen, Trash2, X } from 'lucide-react';
import type { CsHomeHistoryItem } from '../../../types/csHome';
import { historyCardFromItem, type AdviceTone } from './iaUtils';

type IaHistoryDrawerProps = {
  open: boolean;
  onToggle: () => void;
  items: CsHomeHistoryItem[];
  selectedId?: string | null;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  onClearAll?: () => void;
};

const toneClass: Record<AdviceTone, string> = {
  bullish: 'ia-tone-bullish',
  bearish: 'ia-tone-bearish',
  neutral: 'ia-tone-neutral',
};

export const IaHistoryDrawer: React.FC<IaHistoryDrawerProps> = ({
  open,
  onToggle,
  items,
  selectedId,
  onSelect,
  onDelete,
  onClearAll,
}) => (
  <>
    {open ? (
      <div className="ia-history-backdrop lg:hidden" onClick={onToggle} aria-hidden="true" />
    ) : null}

    <aside
      className={`ia-history-rail ${open ? 'ia-history-rail-open' : ''}`}
      aria-label="历史分析"
    >
      <div className="ia-history-rail-bar">
        <button
          type="button"
          onClick={onToggle}
          className="ia-history-toggle"
          aria-expanded={open}
          aria-label={open ? '收起历史分析' : '展开历史分析'}
        >
          {open ? <PanelLeftClose className="h-4 w-4" /> : <PanelLeftOpen className="h-4 w-4" />}
          <History className="h-4 w-4" />
          {!open ? <span className="ia-history-toggle-label">历史分析</span> : null}
          {items.length > 0 ? <span className="ia-history-count">{items.length}</span> : null}
        </button>

        {open ? (
          <>
            <h2 className="ia-history-rail-title">历史分析</h2>
            <div className="ia-history-rail-actions">
              {items.length > 0 && onClearAll ? (
                <button type="button" className="ia-text-btn" onClick={onClearAll}>
                  清空
                </button>
              ) : null}
              <button type="button" className="ia-icon-btn lg:hidden" onClick={onToggle} aria-label="关闭">
                <X className="h-4 w-4" />
              </button>
            </div>
          </>
        ) : null}
      </div>

      {open ? (
        <div className="ia-history-rail-body">
          {items.length === 0 ? (
            <p className="ia-muted text-sm">分析后会自动保存在本机，方便你快速回看。</p>
          ) : (
            <ul className="ia-history-cards">
              {items.map((item) => {
                const card = historyCardFromItem(item);
                const active = card.id === selectedId;
                return (
                  <li key={card.id}>
                    <button
                      type="button"
                      className={`ia-history-card group ${active ? 'ia-history-card-active' : ''}`}
                      onClick={() => onSelect(card.id)}
                    >
                      <div className="ia-history-card-top">
                        <p className="ia-history-card-title">{card.name}</p>
                        <button
                          type="button"
                          className="ia-history-delete"
                          aria-label="删除"
                          onClick={(event) => {
                            event.stopPropagation();
                            onDelete(card.id);
                          }}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                      <div className="ia-history-card-meta">
                        <span className={`ia-advice-pill ${toneClass[card.tone]}`}>
                          {card.adviceShort}
                        </span>
                        <span>评分 {card.score}</span>
                        <span>{card.date}</span>
                      </div>
                      <p className={`ia-history-card-advice ${toneClass[card.tone]}`}>{card.advice}</p>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      ) : null}
    </aside>
  </>
);
