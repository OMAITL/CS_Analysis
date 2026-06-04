import type React from 'react';
import {
  BarChart3,
  Clock,
  Layers,
  LineChart,
  Newspaper,
  Sparkles,
  Target,
} from 'lucide-react';
import type { CsHomeHistoryItem } from '../../../types/csHome';
import { historyCardFromItem } from './iaUtils';

type IaReportPlaceholderProps = {
  historyItems: CsHomeHistoryItem[];
  onSelectHistory: (id: string) => void;
};

const REPORT_FEATURES = [
  {
    icon: Target,
    title: '投资决策',
    desc: 'AI 评分、建议与风险等级，首屏即见结论',
  },
  {
    icon: LineChart,
    title: '评分依据',
    desc: '利好 / 利空因素拆解，情绪与趋势一目了然',
  },
  {
    icon: BarChart3,
    title: '策略点位',
    desc: '买入、止盈、止损区间，辅助实际操作',
  },
  {
    icon: Newspaper,
    title: '市场资讯',
    desc: '事件简讯与利多 / 利空标签，点击展开全文',
  },
] as const;

export const IaReportPlaceholder: React.FC<IaReportPlaceholderProps> = ({
  historyItems,
  onSelectHistory,
}) => (
  <div className="ia-report-placeholder">
    <div className="ia-report-placeholder-hero">
      <div className="ia-report-placeholder-icon">
        <Layers className="h-7 w-7" />
      </div>
      <h2 className="ia-report-placeholder-title">分析报告将显示在这里</h2>
      <p className="ia-report-placeholder-lead">
        在左侧选择饰品并启动分析，Agent 会生成结构化投资决策报告
      </p>
    </div>

    <div className="ia-report-preview-cards">
      <div className="ia-report-preview-card ia-report-preview-card-ghost">
        <span className="ia-report-preview-label">示例 · 决策层</span>
        <div className="ia-report-preview-score">72</div>
        <p className="ia-report-preview-advice">建议观望，等待回调</p>
        <div className="ia-report-preview-tags">
          <span className="ia-tag ia-tag-neutral">中风险</span>
          <span className="ia-tag ia-tag-neutral">震荡偏强</span>
        </div>
      </div>
      <div className="ia-report-preview-card ia-report-preview-card-dim">
        <Sparkles className="h-4 w-4 text-[hsl(var(--primary))]" />
        <p>真实报告包含价格、平台价差、完整 AI 总结等模块</p>
      </div>
    </div>

    <div className="ia-report-features">
      <h3 className="ia-report-features-title">报告包含</h3>
      <ul className="ia-report-features-list">
        {REPORT_FEATURES.map((item) => {
          const Icon = item.icon;
          return (
            <li key={item.title} className="ia-report-feature">
              <div className="ia-report-feature-icon">
                <Icon className="h-4 w-4" />
              </div>
              <div>
                <p className="ia-report-feature-title">{item.title}</p>
                <p className="ia-report-feature-desc">{item.desc}</p>
              </div>
            </li>
          );
        })}
      </ul>
    </div>

    {historyItems.length > 0 ? (
      <div className="ia-report-recent">
        <h3 className="ia-report-recent-title">
          <Clock className="h-4 w-4" />
          最近分析
        </h3>
        <ul className="ia-report-recent-list">
          {historyItems.slice(0, 4).map((item) => {
            const card = historyCardFromItem(item);
            return (
              <li key={card.id}>
                <button
                  type="button"
                  className="ia-report-recent-item"
                  onClick={() => onSelectHistory(card.id)}
                >
                  <span className="ia-report-recent-name">{card.name}</span>
                  <span className="ia-report-recent-meta">
                    评分 {card.score} · {card.adviceShort} · {card.date}
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      </div>
    ) : null}
  </div>
);

export const IaReportLoading: React.FC<{ itemName?: string }> = ({ itemName }) => (
  <div className="ia-report-loading">
    <div className="ia-report-loading-spinner" aria-hidden="true" />
    <h2 className="ia-report-loading-title">Agent 正在分析</h2>
    <p className="ia-report-loading-desc">
      {itemName ? `正在处理「${itemName}」` : '正在抓取行情、检索资讯并生成决策报告'}
    </p>
    <p className="ia-report-loading-hint">通常需要 1–3 分钟，请稍候</p>
  </div>
);
