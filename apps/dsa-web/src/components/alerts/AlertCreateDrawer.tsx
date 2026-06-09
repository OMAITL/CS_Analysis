import type React from 'react';
import { Drawer } from '../common';
import { AlertRuleForm, type AlertRuleFormPreset } from './AlertRuleForm';

type AlertCreateDrawerProps = {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: Parameters<typeof AlertRuleForm>[0]['onSubmit'];
  isSubmitting?: boolean;
  preset?: AlertRuleFormPreset | null;
};

export const AlertCreateDrawer: React.FC<AlertCreateDrawerProps> = ({
  isOpen,
  onClose,
  onSubmit,
  isSubmitting = false,
  preset = null,
}) => (
  <Drawer isOpen={isOpen} onClose={onClose} title="新建告警规则" width="max-w-xl">
    <AlertRuleForm
      key={isOpen ? (preset?.presetKey ?? 'blank') : 'closed'}
      embedded
      csOnly
      preset={preset}
      onSubmit={async (payload) => {
        const ok = await onSubmit(payload);
        if (ok !== false) {
          onClose();
        }
        return ok;
      }}
      isSubmitting={isSubmitting}
    />
  </Drawer>
);
