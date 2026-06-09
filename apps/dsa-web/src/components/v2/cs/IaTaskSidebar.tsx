import type React from 'react';
import { Play, RefreshCw, Settings2 } from 'lucide-react';
import { CsItemSearchInput } from '../../cs/CsItemSearchInput';
import type { CsGoodIdItem } from '../../../types/cs';
import type { CsSkillInfo } from '../../../types/csHome';
import { AGENT_PRESET_TASKS } from './iaAgentConfig';

type IaTaskSidebarProps = {
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
  isAnalyzing: boolean;
  inputError?: boolean;
  onSubmit: () => void;
  onPickTask: (query: string) => void;
};

export const IaTaskSidebar: React.FC<IaTaskSidebarProps> = ({
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
  isAnalyzing,
  inputError,
  onSubmit,
  onPickTask,
}) => {
  const strategyOptions = [
    { id: '', name: '默认策略' },
    ...csSkills.map((skill) => ({ id: skill.id, name: skill.displayName })),
  ];
  const activeStrategy = strategyOptions.find((opt) => opt.id === selectedSkillId) ?? strategyOptions[0];

  return (
    <aside className="ia-task-sidebar">
      <section className="ia-task-panel">
        <div className="ia-task-panel-head">
          <h2 className="ia-task-panel-title">发起分析任务</h2>
          <span className="ia-task-panel-meta">
            <Settings2 className="h-3.5 w-3.5" />
            Agent 配置
          </span>
        </div>

        <label className="ia-task-field">
          <span>目标饰品</span>
          <CsItemSearchInput
            value={query}
            onChange={onQueryChange}
            selectedItem={selectedItem}
            onSelect={onSelectItem}
            onSubmit={onSubmit}
            disabled={isAnalyzing}
            hasError={inputError}
            placeholder="名称 / 皮肤，搜索并选择饰品"
          />
        </label>

        <div className="ia-task-config-grid">
          <label className="ia-task-field">
            <span>价格平台</span>
            <select
              className="ia-select w-full"
              value={platform}
              onChange={(e) => onPlatformChange(e.target.value)}
              disabled={isAnalyzing}
            >
              <option value="yyyp">悠悠有品</option>
              <option value="buff">BUFF</option>
              <option value="steam">Steam</option>
            </select>
          </label>
          <label className="ia-task-field">
            <span>决策 Skill</span>
            <select
              className="ia-select w-full"
              value={selectedSkillId}
              onChange={(e) => onSelectedSkillIdChange(e.target.value)}
              disabled={isAnalyzing}
            >
              {strategyOptions.map((opt) => (
                <option key={opt.id || 'default'} value={opt.id}>
                  {opt.name}
                </option>
              ))}
            </select>
          </label>
        </div>

        <label className="ia-task-checkbox">
          <input
            type="checkbox"
            checked={refreshCrawl}
            onChange={(e) => onRefreshCrawlChange(e.target.checked)}
            disabled={isAnalyzing}
          />
          <span>
            <RefreshCw className="h-3.5 w-3.5" />
            强制刷新爬虫数据（更慢，数据更新）
          </span>
        </label>

        <div className="ia-task-summary">
          <span>本次任务：</span>
          <strong>{selectedItem?.name || query.trim() || '未指定饰品'}</strong>
          <span className="ia-muted">·</span>
          <span>{activeStrategy.name}</span>
        </div>

        <button
          type="button"
          className="ia-btn-primary ia-task-submit"
          disabled={!query.trim() || isAnalyzing}
          onClick={onSubmit}
        >
          {isAnalyzing ? (
            <>
              <LoaderPulse small />
              Agent 分析中…
            </>
          ) : (
            <>
              <Play className="h-4 w-4" />
              启动 Agent 分析
            </>
          )}
        </button>
      </section>

      <section className="ia-preset-panel">
        <h3 className="ia-preset-title">预设分析任务</h3>
        <p className="ia-preset-desc">一键下发任务，Agent 自动完成分析</p>
        <div className="ia-preset-grid ia-preset-grid-stack">
          {AGENT_PRESET_TASKS.map((task) => (
            <button
              key={task.id}
              type="button"
              className="ia-preset-card"
              disabled={isAnalyzing}
              onClick={() => onPickTask(task.query)}
            >
              <span className="ia-preset-card-title">{task.title}</span>
              <span className="ia-preset-card-focus">{task.focus}</span>
            </button>
          ))}
        </div>
      </section>
    </aside>
  );
};

const LoaderPulse: React.FC<{ small?: boolean }> = ({ small }) => (
  <span className={`ia-loader-pulse ${small ? 'ia-loader-pulse-sm' : ''}`} aria-hidden="true">
    <span />
    <span />
    <span />
  </span>
);
