import type React from 'react';
import { Badge, Button, ScrollArea } from '../common';
import { DashboardPanelHeader, DashboardStateBlock } from '../dashboard';
import type { CsHomeHistoryItem } from '../../types/csHome';

type CsHistoryListProps = {
  items: CsHomeHistoryItem[];
  selectedId?: string | null;
  onItemClick: (id: string) => void;
  onDeleteItem: (id: string) => void;
  onClearAll?: () => void;
  className?: string;
};

export const CsHistoryList: React.FC<CsHistoryListProps> = ({
  items,
  selectedId,
  onItemClick,
  onDeleteItem,
  onClearAll,
  className = '',
}) => (
  <div className={`flex min-h-0 flex-col overflow-hidden ${className}`}>
    <DashboardPanelHeader
      title="历史分析"
      actions={items.length > 0 && onClearAll ? (
        <Button type="button" variant="ghost" size="sm" onClick={onClearAll}>
          清空
        </Button>
      ) : undefined}
    />
    <ScrollArea className="min-h-0 flex-1">
      {items.length === 0 ? (
        <DashboardStateBlock
          title="暂无记录"
          description="分析结果会保存在本机浏览器中。"
          className="py-8"
        />
      ) : (
        <ul className="space-y-1.5 pr-1">
          {items.map((item) => {
            const active = item.id === selectedId;
            return (
              <li key={item.id}>
                <button
                  type="button"
                  onClick={() => onItemClick(item.id)}
                  className={`w-full rounded-xl border px-3 py-2.5 text-left transition-colors ${
                    active
                      ? 'border-[var(--nav-active-border)] bg-[var(--nav-active-bg)]'
                      : 'border-transparent hover:bg-hover'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <span className="line-clamp-2 text-sm font-medium text-foreground">
                      {item.itemName}
                    </span>
                    <Badge variant="warning" className="shrink-0 text-[10px]">
                      {item.signalScore}
                    </Badge>
                  </div>
                  <p className="mt-1 truncate text-xs text-muted-text">
                    {item.buySignal} · {item.platform.toUpperCase()}
                  </p>
                </button>
                <button
                  type="button"
                  className="mt-0.5 w-full text-right text-[10px] text-muted-text hover:text-danger"
                  onClick={(event) => {
                    event.stopPropagation();
                    onDeleteItem(item.id);
                  }}
                >
                  删除
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </ScrollArea>
  </div>
);
