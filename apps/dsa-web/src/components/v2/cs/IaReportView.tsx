import type React from 'react';
import { ArrowLeft, RotateCw } from 'lucide-react';
import type { CsItemAnalyzeResponse } from '../../../types/cs';
import { IaActionZones } from './IaActionZones';
import { IaAiReport } from './IaAiReport';
import { IaDecisionHero } from './IaDecisionHero';
import { IaNewsBriefs } from './IaNewsBriefs';
import { IaPlatformArbitrage } from './IaPlatformArbitrage';
import { IaScoreBreakdown } from './IaScoreBreakdown';
import { IaSentimentSection } from './IaSentimentBar';

type IaReportViewProps = {
  data: CsItemAnalyzeResponse;
  onBack: () => void;
  onReanalyze: () => void;
  isAnalyzing?: boolean;
};

export const IaReportView: React.FC<IaReportViewProps> = ({
  data,
  onBack,
  onReanalyze,
  isAnalyzing = false,
}) => (
  <div className="ia-results">
    <div className="ia-results-toolbar">
      <button type="button" className="ia-text-btn" onClick={onBack}>
        <ArrowLeft className="h-4 w-4" />
        新分析
      </button>
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

    <div className="ia-results-stack">
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
