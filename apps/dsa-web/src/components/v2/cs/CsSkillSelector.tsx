import type React from 'react';
import { useMemo } from 'react';
import type { CsSkillInfo } from '../../../types/csHome';
import {
  findCsSkill,
  groupCsSkills,
  resolveSkillDisplayName,
} from '../../../utils/csSkillUi';

type CsSkillSelectorBaseProps = {
  skills: CsSkillInfo[];
  recommendedIds?: string[];
  categoryLabels?: Record<string, string>;
  disabled?: boolean;
};

type CsSkillSelectProps = CsSkillSelectorBaseProps & {
  variant: 'select';
  value: string;
  onChange: (skillId: string) => void;
};

type CsSkillChipsProps = CsSkillSelectorBaseProps & {
  variant: 'chips';
  selectedIds: string[];
  onChange: (skillIds: string[]) => void;
  maxSelected?: number;
};

export type CsSkillSelectorProps = CsSkillSelectProps | CsSkillChipsProps;

export const CsSkillSelector: React.FC<CsSkillSelectorProps> = (props) => {
  const { skills, recommendedIds, categoryLabels, disabled } = props;
  const groups = useMemo(
    () => groupCsSkills(skills, { recommendedIds, categoryLabels }),
    [skills, recommendedIds, categoryLabels],
  );
  if (props.variant === 'select') {
    const activeSkill = findCsSkill(skills, props.value);
    return (
      <div className="ia-skill-selector">
        <select
          className="ia-select w-full"
          value={props.value}
          onChange={(event) => props.onChange(event.target.value)}
          disabled={disabled}
        >
          <option value="">智能默认 — 多头趋势（不用选）</option>
          {groups.map((group) => (
            <optgroup key={group.key} label={group.label}>
              {group.items.map((skill) => (
                <option key={skill.id} value={skill.id}>
                  {skill.displayName}
                </option>
              ))}
            </optgroup>
          ))}
        </select>
        <p className="ia-skill-hint">
          {activeSkill?.description
            ?? '不选也可以：系统默认用「多头趋势」分析，适合大多数「能不能买」类问题。'}
        </p>
      </div>
    );
  }

  const { selectedIds, onChange, maxSelected = 3 } = props;
  const toggleSkill = (skillId: string) => {
    if (selectedIds.includes(skillId)) {
      onChange(selectedIds.filter((id) => id !== skillId));
      return;
    }
    if (selectedIds.length >= maxSelected) {
      return;
    }
    onChange([...selectedIds, skillId]);
  };

  return (
    <div className="ia-skill-selector">
      <p className="ia-skill-hint ia-skill-hint-top">
        不选也可以，Agent 会按问题自动分析。需要指定视角时，优先点「推荐」里的策略。
      </p>
      {selectedIds.length > 0 ? (
        <p className="ia-skill-active-summary">
          已选 {selectedIds.length}/{maxSelected}：
          {selectedIds.map((id) => resolveSkillDisplayName(skills, id, id)).join('、')}
        </p>
      ) : null}
      {groups.map((group) => (
        <div key={group.key} className="ia-skill-group">
          <p className="ia-skill-group-label">{group.label}</p>
          <div className="ia-skill-chips">
            {group.items.map((skill) => {
              const selected = selectedIds.includes(skill.id);
              const atLimit = !selected && selectedIds.length >= maxSelected;
              return (
                <button
                  key={skill.id}
                  type="button"
                  title={skill.description}
                  className={`ia-chip ${selected ? 'ring-2 ring-[hsl(var(--primary))]' : ''}`}
                  disabled={disabled || atLimit}
                  onClick={() => toggleSkill(skill.id)}
                >
                  {skill.displayName}
                </button>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
};
