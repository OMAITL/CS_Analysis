import type React from 'react';
import { useState } from 'react';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { CsItemAnalyzeResponse } from '../../../types/cs';
import {
  buildReportFromData,
  buildUserFacingReportSections,
  type ReportSummaryBlock,
} from './iaUtils';

type IaAiReportProps = {
  data: CsItemAnalyzeResponse;
};

type ReportCardVariant = 'conclusion' | 'risk' | 'watch';

const CARD_LABELS: Record<ReportCardVariant, string> = {
  conclusion: '结论',
  risk: '风险提示',
  watch: '后续观察',
};

const ReportSummaryCard: React.FC<{ variant: ReportCardVariant; block: ReportSummaryBlock }> = ({
  variant,
  block,
}) => {
  const hasContent = Boolean(block.lead) || block.items.length > 0;
  if (!hasContent) {
    return null;
  }

  return (
    <div className={`ia-report-block ia-report-block-${variant}`}>
      <p className="ia-report-block-label">{CARD_LABELS[variant]}</p>
      {block.lead ? <p className="ia-report-lead">{block.lead}</p> : null}
      {block.items.length > 0 ? (
        <ul className="ia-report-points">
          {block.items.map((item) => (
            <li key={`${item.label ?? 'item'}-${item.text}`} className="ia-report-point">
              {item.label ? <span className="ia-report-point-label">{item.label}</span> : null}
              <span className="ia-report-point-text">{item.text}</span>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
};

export const IaAiReport: React.FC<IaAiReportProps> = ({ data }) => {
  const [open, setOpen] = useState(false);
  const report = buildReportFromData(data);
  const sections = buildUserFacingReportSections(data);

  if (!sections.expandedMarkdown && !report.summary.analysisSummary) {
    return null;
  }

  return (
    <section className="ia-card ia-ai-report-card">
      <button
        type="button"
        className="ia-report-toggle"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        <h3 className="ia-section-title ia-section-title-inline">AI 总结报告</h3>
        <span className="ia-muted text-sm">{open ? '收起详情' : '展开详情'}</span>
      </button>

      <div className="ia-report-summary-grid">
        <ReportSummaryCard variant="conclusion" block={sections.conclusion} />
        <ReportSummaryCard variant="risk" block={sections.risks} />
        <ReportSummaryCard variant="watch" block={sections.watch} />
      </div>

      {open && sections.expandedMarkdown ? (
        <div className="ia-report-full ia-markdown ia-markdown-report">
          <Markdown remarkPlugins={[remarkGfm]}>{sections.expandedMarkdown}</Markdown>
        </div>
      ) : null}
    </section>
  );
};
