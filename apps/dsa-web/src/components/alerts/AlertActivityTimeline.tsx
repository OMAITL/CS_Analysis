import type React from 'react';
import { useState } from 'react';
import { ChevronDown, Clock3 } from 'lucide-react';
import { Button, Card, EmptyState } from '../common';
import type { AlertActivityItem } from '../../utils/csAlertMonitor';
import { cn } from '../../utils/cn';

type AlertActivityTimelineProps = {
  items: AlertActivityItem[];
  initialLimit?: number;
};

const toneClass: Record<AlertActivityItem['tone'], string> = {
  urgent: 'bg-danger',
  watch: 'bg-warning',
  info: 'bg-cyan',
  neutral: 'bg-muted-text',
};

export const AlertActivityTimeline: React.FC<AlertActivityTimelineProps> = ({
  items,
  initialLimit = 5,
}) => {
  const [expanded, setExpanded] = useState(false);
  const visibleItems = expanded ? items : items.slice(0, initialLimit);
  const hasMore = items.length > initialLimit;

  return (
    <Card title="今日动态" subtitle="触发与规则变更" variant="bordered" padding="md">
      {items.length === 0 ? (
        <EmptyState
          icon={<Clock3 className="h-6 w-6" />}
          title="今日暂无动态"
          description="告警触发、规则创建后会出现在这里。"
        />
      ) : (
        <>
          <ol className="space-y-2.5">
            {visibleItems.map((item) => (
              <li key={item.id} className="flex gap-3">
                <div className="flex w-12 shrink-0 flex-col items-end pt-0.5">
                  <span className="font-mono text-xs text-secondary-text">{item.timeLabel}</span>
                </div>
                <div className="relative flex min-w-0 flex-1 gap-3 border-l border-border/60 pl-3">
                  <span className={cn('absolute -left-[5px] top-1.5 h-2 w-2 rounded-full', toneClass[item.tone])} />
                  <p className="min-w-0 text-sm text-foreground">{item.title}</p>
                </div>
              </li>
            ))}
          </ol>
          {hasMore ? (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="mt-2 w-full"
              onClick={() => setExpanded((value) => !value)}
            >
              <ChevronDown className={cn('h-4 w-4 transition-transform', expanded && 'rotate-180')} />
              {expanded ? '收起' : `展开全部 ${items.length} 条`}
            </Button>
          ) : null}
        </>
      )}
    </Card>
  );
};
