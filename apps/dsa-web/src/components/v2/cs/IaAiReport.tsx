import type React from 'react';
import { useState } from 'react';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { CsItemAnalyzeResponse } from '../../../types/cs';
import { buildReportFromData, stripInternalMarkdown } from './iaUtils';

type IaAiReportProps = {
  data: CsItemAnalyzeResponse;
};

function extractSection(markdown: string, heading: string): string {
  const regex = new RegExp(`##\\s*${heading}\\s*\\n+([\\s\\S]*?)(?=\\n##\\s|$)`, 'i');
  const match = markdown.match(regex);
  return match?.[1]?.trim() ?? '';
}

export const IaAiReport: React.FC<IaAiReportProps> = ({ data }) => {
  const [open, setOpen] = useState(false);
  const report = buildReportFromData(data);
  const raw = stripInternalMarkdown(data.reportMarkdown || '');
  const conclusion =
    extractSection(raw, '核心结论')
    || report.summary.analysisSummary
    || '暂无结论摘要';
  const risks =
    extractSection(raw, '风险提示')
    || data.trend.riskFactors.slice(0, 3).join('；')
    || '注意波动与流动性风险';
  const watch =
    extractSection(raw, '操作建议')
    || report.summary.operationAdvice
    || '持续观察价格与成交量变化';

  if (!raw && !report.summary.analysisSummary) {
    return null;
  }

  return (
    <section className="ia-card">
      <button
        type="button"
        className="ia-report-toggle"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        <h3 className="ia-section-title">AI 总结报告</h3>
        <span className="ia-muted text-sm">{open ? '收起' : '展开'}</span>
      </button>

      <div className="ia-report-summary-always">
        <div className="ia-report-block">
          <p className="ia-report-block-label">结论</p>
          <p>{conclusion}</p>
        </div>
        <div className="ia-report-block">
          <p className="ia-report-block-label">风险提示</p>
          <p>{risks}</p>
        </div>
        <div className="ia-report-block">
          <p className="ia-report-block-label">后续观察</p>
          <p>{watch}</p>
        </div>
      </div>

      {open && raw ? (
        <div className="ia-report-full ia-markdown">
          <Markdown remarkPlugins={[remarkGfm]}>{raw}</Markdown>
        </div>
      ) : null}
    </section>
  );
};
