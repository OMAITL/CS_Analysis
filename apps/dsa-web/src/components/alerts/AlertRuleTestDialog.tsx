import type React from 'react';
import { createPortal } from 'react-dom';
import { AlertCircle, CheckCircle2, X } from 'lucide-react';
import type { ParsedApiError } from '../../api/error';
import { Badge } from '../common';
import type { AlertRuleTestResponse } from '../../types/alerts';
import { cn } from '../../utils/cn';

type AlertRuleTestDialogProps = {
  isOpen: boolean;
  onClose: () => void;
  ruleName?: string;
  result?: AlertRuleTestResponse | null;
  error?: ParsedApiError | null;
};

function formatObservedValue(value: unknown): string | null {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return `¥${value.toFixed(2)}`;
  }
  if (typeof value === 'string' && value.trim()) {
    return value.trim();
  }
  return null;
}

function statusMeta(result: AlertRuleTestResponse): {
  label: string;
  badgeVariant: 'success' | 'warning' | 'danger';
  tone: 'success' | 'warning' | 'danger';
} {
  if (result.status === 'evaluation_error') {
    return { label: '评估失败', badgeVariant: 'danger', tone: 'danger' };
  }
  if (result.triggered) {
    return { label: '已触发', badgeVariant: 'success', tone: 'success' };
  }
  return { label: '未触发', badgeVariant: 'warning', tone: 'warning' };
}

export const AlertRuleTestDialog: React.FC<AlertRuleTestDialogProps> = ({
  isOpen,
  onClose,
  ruleName,
  result,
  error,
}) => {
  if (!isOpen) return null;

  const meta = result ? statusMeta(result) : null;
  const observed = result ? formatObservedValue(result.observedValue) : null;

  const dialog = (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={onClose}
      role="presentation"
    >
      <div
        className="mx-4 w-full max-w-md rounded-xl border border-border/70 bg-elevated p-5 shadow-2xl"
        onClick={(event) => event.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="alert-test-dialog-title"
      >
        <div className="mb-4 flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h3 id="alert-test-dialog-title" className="text-base font-semibold text-foreground">
              测试结果
            </h3>
            {ruleName ? (
              <p className="mt-1 truncate text-xs text-secondary-text">{ruleName}</p>
            ) : null}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1 text-secondary-text transition-colors hover:bg-hover hover:text-foreground"
            aria-label="关闭"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {error ? (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0 text-danger" />
              <span className="text-sm font-medium text-danger">{error.title}</span>
            </div>
            <p className="text-sm leading-relaxed text-secondary-text">{error.message}</p>
          </div>
        ) : null}

        {result && meta ? (
          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant={meta.badgeVariant}>{meta.label}</Badge>
              {result.evaluatedCount != null ? (
                <span className="text-xs text-secondary-text">
                  评估 {result.evaluatedCount} 个目标
                </span>
              ) : null}
            </div>

            <p className="text-sm leading-relaxed text-foreground">{result.message}</p>

            <dl className="grid grid-cols-2 gap-2 rounded-lg border border-border/50 bg-card/60 p-3 text-xs">
              {observed ? (
                <div>
                  <dt className="text-secondary-text">观测值</dt>
                  <dd className="mt-0.5 font-medium tabular-nums text-cyan">{observed}</dd>
                </div>
              ) : null}
              {result.triggeredCount != null ? (
                <div>
                  <dt className="text-secondary-text">触发</dt>
                  <dd className="mt-0.5 font-medium tabular-nums text-foreground">{result.triggeredCount}</dd>
                </div>
              ) : null}
              {result.degradedCount != null && result.degradedCount > 0 ? (
                <div>
                  <dt className="text-secondary-text">降级</dt>
                  <dd className="mt-0.5 font-medium tabular-nums text-warning">{result.degradedCount}</dd>
                </div>
              ) : null}
              {result.skippedCount != null && result.skippedCount > 0 ? (
                <div>
                  <dt className="text-secondary-text">跳过</dt>
                  <dd className="mt-0.5 font-medium tabular-nums text-secondary-text">{result.skippedCount}</dd>
                </div>
              ) : null}
            </dl>

            {result.targetResults && result.targetResults.length > 0 ? (
              <div className="max-h-40 space-y-2 overflow-y-auto rounded-lg border border-border/50 bg-card/40 p-3">
                {result.targetResults.map((item) => (
                  <div key={`${item.target}-${item.status}`} className="text-xs leading-relaxed">
                    <div className="flex items-center gap-2">
                      <CheckCircle2
                        className={cn(
                          'h-3.5 w-3.5 shrink-0',
                          item.triggered ? 'text-success' : 'text-secondary-text/60',
                        )}
                      />
                      <span className="font-medium text-foreground">
                        {item.displayTarget ?? item.target}
                      </span>
                      <span className="text-secondary-text">
                        {item.triggered ? '已触发' : '未触发'}
                      </span>
                    </div>
                    {item.message ? (
                      <p className="mt-0.5 pl-5 text-secondary-text">{item.message}</p>
                    ) : null}
                  </div>
                ))}
              </div>
            ) : null}

            <p className="text-[11px] text-secondary-text/80">
              此为干跑测试，不会写入触发历史或发送通知。
            </p>
          </div>
        ) : null}

        <div className="mt-5 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-border/70 px-4 py-2 text-sm font-medium text-secondary-text transition-colors hover:bg-hover hover:text-foreground"
          >
            关闭
          </button>
        </div>
      </div>
    </div>
  );

  return createPortal(dialog, document.body);
};
