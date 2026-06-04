import type React from 'react';
import { useEffect, useState } from 'react';
import { Check, Circle, Loader2 } from 'lucide-react';
import { AGENT_PIPELINE_STEPS, type AgentPipelineStep } from './iaAgentConfig';
import type { AgentStepStatus } from './useAgentRunProgress';

type IaAgentPipelineProps = {
  isRunning: boolean;
  onActiveStep?: (step: AgentPipelineStep | null) => void;
};

const STEP_MS = 7000;

function buildStatuses(activeIndex: number, isRunning: boolean): AgentStepStatus[] {
  return AGENT_PIPELINE_STEPS.map((_, index) => {
    if (!isRunning) {
      return 'pending';
    }
    if (index < activeIndex) {
      return 'done';
    }
    if (index === activeIndex) {
      return 'active';
    }
    return 'pending';
  });
}

const statusIcon: Record<AgentStepStatus, React.ReactNode> = {
  pending: <Circle className="h-3.5 w-3.5 opacity-40" />,
  active: <Loader2 className="h-3.5 w-3.5 animate-spin text-[hsl(var(--primary))]" />,
  done: <Check className="h-3.5 w-3.5 text-[var(--ia-bull)]" />,
};

/** Remount with a new `key` each run to reset step index. */
export const IaAgentPipelineTracker: React.FC<IaAgentPipelineProps> = ({
  isRunning,
  onActiveStep,
}) => {
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    if (!isRunning) {
      onActiveStep?.(null);
      return undefined;
    }

    onActiveStep?.(AGENT_PIPELINE_STEPS[0] ?? null);

    const timer = window.setInterval(() => {
      setActiveIndex((prev) => Math.min(prev + 1, AGENT_PIPELINE_STEPS.length - 1));
    }, STEP_MS);

    return () => window.clearInterval(timer);
  }, [isRunning, onActiveStep]);

  useEffect(() => {
    if (!isRunning) {
      return;
    }
    onActiveStep?.(AGENT_PIPELINE_STEPS[activeIndex] ?? null);
  }, [activeIndex, isRunning, onActiveStep]);

  const stepStatuses = buildStatuses(activeIndex, isRunning);
  const progressPct = Math.round(((activeIndex + 0.35) / AGENT_PIPELINE_STEPS.length) * 100);

  return (
    <IaAgentPipelineView
      stepStatuses={stepStatuses}
      isRunning={isRunning}
      progressPct={progressPct}
      activeStep={AGENT_PIPELINE_STEPS[activeIndex] ?? null}
    />
  );
};

type IaAgentPipelineViewProps = {
  stepStatuses: AgentStepStatus[];
  isRunning: boolean;
  progressPct: number;
  activeStep: AgentPipelineStep | null;
};

const IaAgentPipelineView: React.FC<IaAgentPipelineViewProps> = ({
  stepStatuses,
  isRunning,
  progressPct,
  activeStep,
}) => (
  <section className="ia-agent-panel">
    <div className="ia-agent-panel-head">
      <div>
        <h2 className="ia-agent-panel-title">分析流水线</h2>
        <p className="ia-agent-panel-desc">Agent 按序调用工具，不是单次 LLM 问答</p>
      </div>
      {isRunning ? (
        <span className="ia-agent-run-badge">
          <Loader2 className="h-3 w-3 animate-spin" />
          运行中 {progressPct}%
        </span>
      ) : (
        <span className="ia-agent-idle-badge">待命</span>
      )}
    </div>

    {isRunning ? (
      <div className="ia-agent-progress-track" aria-hidden="true">
        <div className="ia-agent-progress-fill" style={{ width: `${progressPct}%` }} />
      </div>
    ) : null}

    {isRunning && activeStep ? (
      <p className="ia-agent-current-step">
        当前：
        <strong>{activeStep.label}</strong>
        <code>{activeStep.tool}</code>
      </p>
    ) : null}

    <ol className="ia-agent-steps">
      {AGENT_PIPELINE_STEPS.map((step, index) => {
        const status = stepStatuses[index] ?? 'pending';
        const Icon = step.icon;
        return (
          <li key={step.id} className={`ia-agent-step ia-agent-step-${status}`}>
            <div className="ia-agent-step-icon-wrap">{statusIcon[status]}</div>
            <div className="ia-agent-step-body">
              <div className="ia-agent-step-top">
                <Icon className="h-4 w-4 shrink-0 opacity-70" />
                <span className="ia-agent-step-label">{step.label}</span>
                <code className="ia-agent-step-tool">{step.tool}</code>
              </div>
              <p className="ia-agent-step-desc">{step.description}</p>
            </div>
          </li>
        );
      })}
    </ol>
  </section>
);

/** Idle pipeline (all pending). */
export const IaAgentPipeline: React.FC = () => (
  <IaAgentPipelineView
    stepStatuses={buildStatuses(0, false)}
    isRunning={false}
    progressPct={0}
    activeStep={null}
  />
);
