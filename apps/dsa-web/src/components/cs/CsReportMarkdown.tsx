import type React from 'react';
import { useState } from 'react';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Card } from '../common';

type CsReportMarkdownProps = {
  content: string;
  reportSource: string;
};

const SOURCE_LABELS: Record<string, string> = {
  llm: '模型生成',
  template: '规则模板',
  none: '无',
};

export const CsReportMarkdown: React.FC<CsReportMarkdownProps> = ({ content, reportSource }) => {
  const [expanded, setExpanded] = useState(false);

  if (!content.trim()) {
    return null;
  }

  const sourceLabel = SOURCE_LABELS[reportSource] ?? reportSource;

  return (
    <Card padding="md" className="animate-fade-in">
      <button
        type="button"
        onClick={() => setExpanded((open) => !open)}
        className="flex w-full items-center justify-between gap-2 text-left"
        aria-expanded={expanded}
      >
        <span className="label-uppercase">完整分析报告</span>
        <span className="flex items-center gap-2 text-xs text-muted-text">
          <span>{sourceLabel}</span>
          <span aria-hidden="true">{expanded ? '收起' : '展开'}</span>
        </span>
      </button>
      {expanded ? (
        <div
          className="home-markdown-prose prose prose-invert prose-sm mt-4 max-w-none
            prose-headings:text-foreground prose-headings:font-semibold
            prose-p:leading-relaxed prose-strong:text-foreground
            prose-li:my-1 prose-ul:my-2
            whitespace-pre-line break-words"
        >
          <Markdown remarkPlugins={[remarkGfm]}>{content}</Markdown>
        </div>
      ) : null}
    </Card>
  );
};
