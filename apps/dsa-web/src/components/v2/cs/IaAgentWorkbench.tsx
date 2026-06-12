import type React from 'react';
import type { CsItemAnalyzeResponse } from '../../../types/cs';
import type { CsGoodIdItem } from '../../../types/cs';
import type { CsHomeHistoryItem, CsSkillInfo } from '../../../types/csHome';
import { IaReportPanel } from './IaReportPanel';
import { IaReportPlaceholder } from './IaReportPlaceholder';
import { IaTaskSidebar } from './IaTaskSidebar';

type IaAgentWorkbenchProps = {
  query: string;
  onQueryChange: (value: string) => void;
  selectedItem: CsGoodIdItem | null;
  onSelectItem: (item: CsGoodIdItem | null) => void;
  platform: string;
  onPlatformChange: (value: string) => void;
  refreshCrawl: boolean;
  onRefreshCrawlChange: (value: boolean) => void;
  selectedSkillId: string;
  onSelectedSkillIdChange: (value: string) => void;
  csSkills: CsSkillInfo[];
  recommendedSkillIds?: string[];
  categoryLabels?: Record<string, string>;
  isAnalyzing: boolean;
  inputError?: boolean;
  onSubmit: () => void;
  onPickTask: (query: string, skillId?: string) => void;
  onReanalyze: () => void;
  result: CsItemAnalyzeResponse | null;
  historyItems: CsHomeHistoryItem[];
  onSelectHistory: (id: string) => void;
};

export const IaAgentWorkbench: React.FC<IaAgentWorkbenchProps> = ({
  query,
  onQueryChange,
  selectedItem,
  onSelectItem,
  platform,
  onPlatformChange,
  refreshCrawl,
  onRefreshCrawlChange,
  selectedSkillId,
  onSelectedSkillIdChange,
  csSkills,
  recommendedSkillIds,
  categoryLabels,
  isAnalyzing,
  inputError,
  onSubmit,
  onPickTask,
  onReanalyze,
  result,
  historyItems,
  onSelectHistory,
}) => (
  <div className="ia-workbench ia-workbench-split">
    <div className="ia-split-layout">
      <IaTaskSidebar
        query={query}
        onQueryChange={onQueryChange}
        selectedItem={selectedItem}
        onSelectItem={onSelectItem}
        platform={platform}
        onPlatformChange={onPlatformChange}
        refreshCrawl={refreshCrawl}
        onRefreshCrawlChange={onRefreshCrawlChange}
        selectedSkillId={selectedSkillId}
        onSelectedSkillIdChange={onSelectedSkillIdChange}
        csSkills={csSkills}
        recommendedSkillIds={recommendedSkillIds}
        categoryLabels={categoryLabels}
        isAnalyzing={isAnalyzing}
        inputError={inputError}
        onSubmit={onSubmit}
        onPickTask={onPickTask}
      />

      <main className="ia-split-report">
        {result || (isAnalyzing && !result) ? (
          <IaReportPanel
            data={result}
            isAnalyzing={isAnalyzing}
            analyzingItemName={selectedItem?.name || query.trim() || undefined}
            onReanalyze={onReanalyze}
          />
        ) : (
          <IaReportPlaceholder
            historyItems={historyItems}
            onSelectHistory={onSelectHistory}
          />
        )}
      </main>
    </div>
  </div>
);
