import type React from 'react';
import { Link } from 'react-router-dom';
import { MessageSquareQuote, RotateCw } from 'lucide-react';
import type { CsItemAnalyzeResponse } from '../../../types/cs';
import { IaActionZones } from './IaActionZones';
import { IaAiReport } from './IaAiReport';
import { IaDecisionHero } from './IaDecisionHero';
import { IaNewsBriefs } from './IaNewsBriefs';
import { IaPlatformArbitrage } from './IaPlatformArbitrage';
import { IaReportLoading } from './IaReportPlaceholder';
import { IaScoreBreakdown } from './IaScoreBreakdown';
import { IaSentimentSection } from './IaSentimentBar';

type IaReportPanelProps = {
  data: CsItemAnalyzeResponse | null;
  isAnalyzing: boolean;
  analyzingItemName?: string;
  onReanalyze: () => void;
};

export const IaReportPanel: React.FC<IaReportPanelProps> = ({
  data,
  isAnalyzing,
  analyzingItemName,
  onReanalyze,
}) => {
  if (isAnalyzing && !data) {
    return (
      <div className="ia-report-panel">
        <IaReportLoading itemName={analyzingItemName} />
      </div>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <div className="ia-report-panel">
      <div className="ia-report-panel-head">
        <div className="ia-report-panel-head-text">
          <p className="ia-report-panel-kicker">分析报告</p>
          {data.itemName ? (
            <p className="ia-report-panel-subtitle">{data.itemName}</p>
          ) : null}
        </div>
        <div className="ia-report-panel-actions flex flex-wrap gap-2">
          <Link
            to={`/chat?name=${encodeURIComponent(data.itemName)}&platform=${encodeURIComponent(data.platform)}`}
            className="ia-btn-secondary inline-flex items-center gap-2 no-underline"
          >
            <MessageSquareQuote className="h-4 w-4" />
            继续追问
          </Link>
          <button
            type="button"
            className="ia-btn-secondary"
            disabled={isAnalyzing}
            onClick={onReanalyze}
          >
            <RotateCw className={`h-4 w-4 ${isAnalyzing ? 'animate-spin' : ''}`} />
            重新分析
          </button>
        </div>
      </div>

      {isAnalyzing ? (
        <div className="ia-report-panel-updating">
          <LoaderPulse />
          正在更新报告…
        </div>
      ) : null}

      <div className={`ia-results-stack ${isAnalyzing ? 'ia-results-dimmed' : ''}`}>
        <IaDecisionHero data={data} />
        <div className="ia-results-row">
          <IaScoreBreakdown data={data} />
          <IaSentimentSection data={data} />
        </div>
        <IaActionZones data={data} />
        <IaPlatformArbitrage data={data} />
        <IaNewsBriefs items={data.eventIntel ?? []} />
        <IaAiReport data={data} />
      </div>
    </div>
  );
};

const LoaderPulse: React.FC = () => (
  <span className="ia-loader-pulse ia-loader-pulse-sm" aria-hidden="true">
    <span />
    <span />
    <span />
  </span>
);
