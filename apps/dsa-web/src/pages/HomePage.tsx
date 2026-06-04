import type React from 'react';
import { useCallback, useEffect, useState } from 'react';
import { ApiErrorAlert, InlineAlert } from '../components/common';
import { IaAgentWorkbench } from '../components/v2/cs/IaAgentWorkbench';
import { IaHistoryDrawer } from '../components/v2/cs/IaHistoryDrawer';
import { csApi } from '../api/cs';
import { useCsHomeState } from '../hooks/useCsHomeState';
import type { CsSkillInfo } from '../types/csHome';
import '../styles/ia-v2.css';

const HomePage: React.FC = () => {
  const [historyOpen, setHistoryOpen] = useState(false);
  const [csSkills, setCsSkills] = useState<CsSkillInfo[]>([]);

  const {
    query,
    platform,
    refreshCrawl,
    selectedSkillId,
    isAnalyzing,
    error,
    inputError,
    result,
    historyItems,
    selectedHistoryId,
    setQuery,
    setSelectedItem,
    selectedItem,
    setPlatform,
    setRefreshCrawl,
    setSelectedSkillId,
    clearError,
    selectHistoryItem,
    deleteHistoryItem,
    clearHistory,
    submitAnalysis,
  } = useCsHomeState();

  useEffect(() => {
    document.title = 'CS 饰品分析 - DSA';
    setQuery('');
    setSelectedItem(null);
  }, [setQuery, setSelectedItem]);

  useEffect(() => {
    let active = true;
    csApi
      .listSkills()
      .then((response) => {
        if (active) {
          setCsSkills(response.skills);
        }
      })
      .catch(() => {
        if (active) {
          setCsSkills([]);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  const handleSubmit = useCallback(async () => {
    await submitAnalysis();
  }, [submitAnalysis]);

  const handlePickTask = useCallback(
    (text: string) => {
      setQuery(text);
      setSelectedItem(null);
      void submitAnalysis(text);
    },
    [setQuery, setSelectedItem, submitAnalysis],
  );

  const handleSelectHistory = useCallback(
    (id: string) => {
      selectHistoryItem(id);
      setHistoryOpen(false);
    },
    [selectHistoryItem],
  );

  const handleReanalyze = useCallback(() => {
    void submitAnalysis();
  }, [submitAnalysis]);

  return (
    <div className="ia-v2-root flex min-h-0 flex-1 flex-col" data-testid="home-dashboard">
      <div className="ia-v2-shell">
        <IaHistoryDrawer
          open={historyOpen}
          onToggle={() => setHistoryOpen((prev) => !prev)}
          items={historyItems}
          selectedId={selectedHistoryId}
          onSelect={handleSelectHistory}
          onDelete={deleteHistoryItem}
          onClearAll={historyItems.length > 0 ? clearHistory : undefined}
        />

        <div className="ia-v2-main">
          {error ? (
            <div className="px-4 pt-3">
              <ApiErrorAlert error={error} onDismiss={clearError} />
            </div>
          ) : null}

          {inputError ? (
            <div className="px-4 pt-2">
              <InlineAlert variant="warning" message={inputError} />
            </div>
          ) : null}

          <IaAgentWorkbench
            query={query}
            onQueryChange={(value) => {
              setQuery(value);
              setSelectedItem(null);
            }}
            selectedItem={selectedItem}
            onSelectItem={setSelectedItem}
            platform={platform}
            onPlatformChange={setPlatform}
            refreshCrawl={refreshCrawl}
            onRefreshCrawlChange={setRefreshCrawl}
            selectedSkillId={selectedSkillId}
            onSelectedSkillIdChange={setSelectedSkillId}
            csSkills={csSkills}
            isAnalyzing={isAnalyzing}
            inputError={Boolean(inputError)}
            onSubmit={() => void handleSubmit()}
            onPickTask={handlePickTask}
            onReanalyze={handleReanalyze}
            result={result}
            historyItems={historyItems}
            onSelectHistory={handleSelectHistory}
          />
        </div>
      </div>
    </div>
  );
};

export default HomePage;
