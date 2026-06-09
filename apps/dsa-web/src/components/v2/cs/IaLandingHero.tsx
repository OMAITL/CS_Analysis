import type React from 'react';
import { BarChart3, Sparkles } from 'lucide-react';
import { CsItemSearchInput } from '../../cs/CsItemSearchInput';
import type { CsGoodIdItem } from '../../../types/cs';
import { HOT_ITEM_PRESETS, QUICK_EXAMPLES } from './iaUtils';

type IaLandingHeroProps = {
  query: string;
  onQueryChange: (value: string) => void;
  selectedItem: CsGoodIdItem | null;
  onSelectItem: (item: CsGoodIdItem | null) => void;
  platform: string;
  onPlatformChange: (value: string) => void;
  isAnalyzing: boolean;
  inputError?: boolean;
  onSubmit: () => void;
  onPickExample: (text: string) => void;
};

export const IaLandingHero: React.FC<IaLandingHeroProps> = ({
  query,
  onQueryChange,
  selectedItem,
  onSelectItem,
  platform,
  onPlatformChange,
  isAnalyzing,
  inputError,
  onSubmit,
  onPickExample,
}) => (
  <div className="ia-landing">
    <div className="ia-landing-brand">
      <div className="ia-landing-logo">
        <BarChart3 className="h-5 w-5" />
      </div>
      <span className="ia-landing-logo-text">DSA 饰品助手</span>
    </div>

    <div className="ia-landing-hero">
      <div className="ia-landing-badge">
        <Sparkles className="h-3.5 w-3.5" />
        AI 驱动 · 结论优先
      </div>
      <h1 className="ia-landing-title">AI 饰品投资分析助手</h1>
      <p className="ia-landing-subtitle">输入饰品名称或皮肤名称，30 秒获得可执行的投资建议</p>

      <div className="ia-landing-search">
        <CsItemSearchInput
          value={query}
          onChange={onQueryChange}
          selectedItem={selectedItem}
          onSelect={onSelectItem}
          onSubmit={onSubmit}
          disabled={isAnalyzing}
          hasError={inputError}
          placeholder="例如：蝴蝶刀 北方森林、AK-47 火蛇、769"
        />
        <div className="ia-landing-search-actions">
          <select
            className="ia-select"
            value={platform}
            onChange={(e) => onPlatformChange(e.target.value)}
            disabled={isAnalyzing}
            aria-label="价格平台"
          >
            <option value="yyyp">悠悠有品</option>
            <option value="buff">BUFF</option>
            <option value="steam">Steam</option>
          </select>
          <button
            type="button"
            className="ia-btn-primary"
            disabled={!query.trim() || isAnalyzing}
            onClick={onSubmit}
          >
            {isAnalyzing ? '分析中…' : '开始分析'}
          </button>
        </div>
      </div>

      <div className="ia-landing-hot">
        <p className="ia-landing-section-label">热门饰品</p>
        <div className="ia-chip-row">
          {HOT_ITEM_PRESETS.map((item) => (
            <button
              key={item.label}
              type="button"
              className="ia-chip"
              disabled={isAnalyzing}
              onClick={() => onPickExample(item.query)}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      <div className="ia-landing-examples">
        <p className="ia-landing-section-label">快速示例</p>
        <div className="ia-example-list">
          {QUICK_EXAMPLES.map((example) => (
            <button
              key={example}
              type="button"
              className="ia-example-item"
              disabled={isAnalyzing}
              onClick={() => onPickExample(example)}
            >
              {example}
            </button>
          ))}
        </div>
      </div>
    </div>
  </div>
);
