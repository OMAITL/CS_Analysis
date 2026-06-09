import type React from 'react';
import { LayoutTemplate } from 'lucide-react';
import { Button, Card } from '../common';
import { CS_ALERT_RULE_TEMPLATES, type AlertRuleTemplate } from '../../utils/csAlertMonitor';

type AlertRuleTemplatesProps = {
  onSelect: (template: AlertRuleTemplate) => void;
  compact?: boolean;
};

export const AlertRuleTemplates: React.FC<AlertRuleTemplatesProps> = ({ onSelect, compact = false }) => (
  <Card
    title="快捷模板"
    subtitle={compact ? undefined : '一键创建常用监控规则'}
    variant="bordered"
    padding={compact ? 'sm' : 'md'}
  >
    <div className={compact ? 'grid gap-1.5' : 'flex flex-wrap gap-2'}>
      {CS_ALERT_RULE_TEMPLATES.map((template) => (
        <Button
          key={template.id}
          type="button"
          size={compact ? 'xsm' : 'sm'}
          variant="secondary"
          className={compact ? 'w-full justify-start' : undefined}
          onClick={() => onSelect(template)}
        >
          <LayoutTemplate className="h-4 w-4" />
          {template.label}
        </Button>
      ))}
    </div>
    {!compact ? (
      <p className="mt-3 text-xs text-secondary-text">
        点击即可为全部 CS 持仓创建常见监控规则；单饰品规则请用「新建规则」。
      </p>
    ) : null}
  </Card>
);
