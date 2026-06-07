import type React from 'react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { MessageSquarePlus, Send } from 'lucide-react';
import { csApi, type CsChatStreamRequest } from '../api/cs';
import { ApiErrorAlert } from '../components/common';
import { useCsChatStore, type ProgressStep } from '../stores/csChatStore';
import type { CsSkillInfo } from '../types/csHome';
import type { CsItemAnalyzeResponse } from '../types/cs';
import '../styles/ia-v2.css';

type ChatAnswerScope = 'market' | 'portfolio' | 'single_item' | 'general';

const CS_QUICK_QUESTIONS: Array<{ label: string; skill: string; scope: ChatAnswerScope }> = [
  { label: '哪些饰品可能有人在做盘？怎么识别？', skill: 'emotion_cycle', scope: 'market' },
  { label: '我持有的饰品在高位要不要出货？', skill: 'bull_trend', scope: 'portfolio' },
  { label: 'AK-47 火蛇现在适合入手还是观望？', skill: 'bull_trend', scope: 'general' },
  { label: '成交量放大但价格横盘，怎么解读？', skill: 'volume_breakout', scope: 'general' },
  { label: 'BUFF 和悠悠有价差，套利要注意什么？', skill: 'box_oscillation', scope: 'general' },
  { label: '最近哪些刀型或手套热度在上升？', skill: 'dragon_head', scope: 'market' },
];

const MAX_SELECTED_SKILLS = 3;

function getCurrentStage(steps: ProgressStep[]): string {
  if (steps.length === 0) return '正在连接 Agent…';
  const last = steps[steps.length - 1];
  if (last.type === 'thinking') return last.message || 'AI 正在规划分析路径…';
  if (last.type === 'tool_start') return `${last.display_name || last.tool || '工具'}…`;
  if (last.type === 'tool_done') return `${last.display_name || last.tool || '工具'} 完成`;
  if (last.type === 'generating') return last.message || '正在生成回答…';
  return '处理中…';
}

function buildFollowUpContext(data: CsItemAnalyzeResponse | null) {
  if (!data) return undefined;
  const summary = data.report?.summary;
  const parts = [
    summary?.analysisSummary,
    summary?.operationAdvice ? `操作建议：${summary.operationAdvice}` : '',
    summary?.trendPrediction ? `趋势：${summary.trendPrediction}` : '',
    `信号分 ${data.trend.signalScore}，${data.trend.buySignal}`,
  ].filter(Boolean);
  return {
    good_id: data.goodId,
    item_name: data.itemName,
    platform: data.platform,
    previous_analysis_summary: parts.join('\n'),
  };
}

function readFollowUpFromStorage(): CsItemAnalyzeResponse | null {
  try {
    const raw = localStorage.getItem('dsa_cs_home_history_v1');
    if (!raw) return null;
    const items = JSON.parse(raw) as Array<{ result?: CsItemAnalyzeResponse }>;
    return items[0]?.result ?? null;
  } catch {
    return null;
  }
}

const CsChatPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [input, setInput] = useState('');
  const [skills, setSkills] = useState<CsSkillInfo[]>([]);
  const [selectedSkillIds, setSelectedSkillIds] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const followUpContext = useMemo((): CsChatStreamRequest['context'] | undefined => {
    const goodId = searchParams.get('goodId');
    const name = searchParams.get('name') ?? searchParams.get('item');
    const platform = searchParams.get('platform');
    const summary = searchParams.get('summary');

    if (goodId || name) {
      return {
        good_id: goodId ? Number.parseInt(goodId, 10) : undefined,
        item_name: name ?? undefined,
        platform: platform ?? undefined,
        previous_analysis_summary: summary ?? undefined,
      };
    }

    return buildFollowUpContext(readFollowUpFromStorage());
  }, [searchParams]);

  const messages = useCsChatStore((s) => s.messages);
  const loading = useCsChatStore((s) => s.loading);
  const progressSteps = useCsChatStore((s) => s.progressSteps);
  const sessionId = useCsChatStore((s) => s.sessionId);
  const sessions = useCsChatStore((s) => s.sessions);
  const chatError = useCsChatStore((s) => s.chatError);
  const startStream = useCsChatStore((s) => s.startStream);
  const startNewChat = useCsChatStore((s) => s.startNewChat);
  const loadInitialSession = useCsChatStore((s) => s.loadInitialSession);
  const switchSession = useCsChatStore((s) => s.switchSession);
  const clearCompletionBadge = useCsChatStore((s) => s.clearCompletionBadge);

  useEffect(() => {
    document.title = '问饰品 - CS 投资助手';
    void loadInitialSession();
    clearCompletionBadge();
  }, [clearCompletionBadge, loadInitialSession]);

  useEffect(() => {
    let active = true;
    csApi
      .listSkills()
      .then((res) => {
        if (active) setSkills(res.skills);
      })
      .catch(() => {
        if (active) setSkills([]);
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const availableSkillIds = useMemo(() => new Set(skills.map((s) => s.id)), [skills]);

  const quickQuestions = useMemo(
    () => CS_QUICK_QUESTIONS.filter(
      (q) => availableSkillIds.size === 0 || availableSkillIds.has(q.skill),
    ),
    [availableSkillIds],
  );

  const getSkillNames = useCallback(
    (skillIds: string[]) => skillIds.map((id) => skills.find((s) => s.id === id)?.displayName || id),
    [skills],
  );

  const buildRequestContext = useCallback(
    (scope?: ChatAnswerScope): CsChatStreamRequest['context'] | undefined => {
      const summaryOnly = followUpContext?.previous_analysis_summary
        ? { previous_analysis_summary: followUpContext.previous_analysis_summary }
        : undefined;

      if (scope === 'market' || scope === 'portfolio') {
        return { scope, ...summaryOnly };
      }
      if (scope === 'general') {
        // 通用快捷问法：不传历史 good_id，让后端从消息文本识别饰品名
        return { scope: 'general', ...summaryOnly };
      }
      if (scope === 'single_item' && followUpContext) {
        return { scope: 'single_item', ...followUpContext };
      }
      if (followUpContext?.good_id) {
        // 普通输入框发送：只带上一轮文字摘要，不带 good_id，避免覆盖消息里新提到的饰品
        return summaryOnly;
      }
      return scope ? { scope, ...summaryOnly } : summaryOnly;
    },
    [followUpContext],
  );

  const normalizeSelectedSkillIds = useCallback((skillIds: string[]) => {
    const normalized: string[] = [];
    for (const skillId of skillIds) {
      const cleaned = skillId.trim();
      if (cleaned && !normalized.includes(cleaned)) {
        normalized.push(cleaned);
      }
    }
    return normalized.slice(0, MAX_SELECTED_SKILLS);
  }, []);

  const handleSend = useCallback(
    async (
      overrideMessage?: string,
      overrideSkillIds?: string[],
      overrideScope?: ChatAnswerScope,
    ) => {
      const msgText = (overrideMessage ?? input).trim();
      if (!msgText || loading) return;

      const usedSkillIds = normalizeSelectedSkillIds(overrideSkillIds ?? selectedSkillIds);
      const usedSkillNames = usedSkillIds.length > 0 ? getSkillNames(usedSkillIds) : ['通用'];
      const requestContext = buildRequestContext(overrideScope);

      setInput('');
      if (searchParams.toString()) {
        setSearchParams({}, { replace: true });
      }

      await startStream(
        {
          message: msgText,
          session_id: sessionId,
          ...(usedSkillIds.length > 0 ? { skills: usedSkillIds } : {}),
          ...(requestContext ? { context: requestContext } : {}),
        },
        { skillNames: usedSkillNames },
      );
    },
    [
      buildRequestContext,
      getSkillNames,
      input,
      loading,
      normalizeSelectedSkillIds,
      searchParams,
      selectedSkillIds,
      sessionId,
      setSearchParams,
      startStream,
    ],
  );

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      void handleSend();
    }
  };

  const toggleSkill = (skillId: string) => {
    setSelectedSkillIds((prev) => {
      if (prev.includes(skillId)) return prev.filter((id) => id !== skillId);
      if (prev.length >= MAX_SELECTED_SKILLS) return prev;
      return [...prev, skillId];
    });
  };

  const hasMessages = messages.length > 0;
  const contextHint = followUpContext?.item_name;
  const inputPlaceholder = contextHint
    ? `例如：关于「${contextHint}」，当前在高位是否需要减仓或出货？`
    : '例如：火蛇在高位放量上涨，是不是有人在出货？';

  return (
    <div className="ia-v2-root flex min-h-0 flex-1 flex-col" data-testid="chat-workspace">
      <div className="ia-chat-v2 ia-chat-v2-with-sidebar">
        <aside className="ia-chat-sidebar hidden lg:flex">
          <div className="ia-chat-sidebar-head">
            <span>会话</span>
            <button type="button" className="ia-text-btn" onClick={() => startNewChat()} title="新对话">
              <MessageSquarePlus className="h-4 w-4" />
            </button>
          </div>
          <div className="ia-chat-session-list" data-testid="chat-session-list-scroll">
            {sessions.length === 0 ? (
              <p className="ia-muted text-xs px-2">暂无历史会话</p>
            ) : (
              sessions.map((session) => (
                <button
                  key={session.session_id}
                  type="button"
                  className={`ia-chat-session-item ${session.session_id === sessionId ? 'active' : ''}`}
                  onClick={() => void switchSession(session.session_id)}
                >
                  {session.title || '新对话'}
                </button>
              ))
            )}
          </div>
        </aside>

        <div className="ia-chat-main flex min-h-0 flex-1 flex-col">
          {chatError ? (
            <div className="mb-3">
              <ApiErrorAlert error={chatError} />
            </div>
          ) : null}

          {!hasMessages ? (
            <div className="ia-chat-hero">
              <h1>问饰品</h1>
              <p className="ia-muted text-sm">
                多轮对话：做盘识别、高位出货、平台价差、趋势解读等。
                需要完整结构化报告请用
                {' '}
                <Link to="/" className="ia-link">饰品工作台</Link>
                。
              </p>
              {contextHint ? (
                <p className="ia-context-hint text-sm">
                  已关联饰品：
                  <strong>{contextHint}</strong>
                  （追问具体饰品时会结合行情快照；问「哪些饰品 / 全市场 / 我持仓」时将自动切换作答范围）
                </p>
              ) : (
                <p className="ia-muted text-xs">
                  支持按问题自动区分：全市场泛问、持仓专属、单品深度追问。
                </p>
              )}
            </div>
          ) : null}

          <div className="ia-chat-messages flex-1 overflow-y-auto" data-testid="chat-message-scroll">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`ia-chat-bubble ${
                  msg.role === 'user' ? 'ia-chat-bubble-user' : 'ia-chat-bubble-assistant'
                }`}
              >
                {msg.role === 'assistant' ? (
                  <Markdown remarkPlugins={[remarkGfm]}>{msg.content || (loading ? '思考中…' : '')}</Markdown>
                ) : (
                  msg.content
                )}
              </div>
            ))}
            {loading && messages[messages.length - 1]?.role === 'user' ? (
              <div className="ia-chat-bubble ia-chat-bubble-assistant ia-muted text-sm">
                {getCurrentStage(progressSteps)}
              </div>
            ) : null}
            <div ref={messagesEndRef} />
          </div>

          {!hasMessages && quickQuestions.length > 0 ? (
            <div className="ia-chat-suggestions">
              {quickQuestions.map((q) => (
                <button
                  key={q.label}
                  type="button"
                  className="ia-chip"
                  disabled={loading}
                  onClick={() => {
                    setSelectedSkillIds([q.skill]);
                    void handleSend(q.label, [q.skill], q.scope);
                  }}
                >
                  {q.label}
                </button>
              ))}
            </div>
          ) : null}

          <div className="ia-chat-input-wrap">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={inputPlaceholder}
              disabled={loading}
              rows={2}
            />
            <div className="ia-chat-input-actions">
              <button type="button" className="ia-text-btn" onClick={() => startNewChat()}>
                新对话
              </button>
              <button
                type="button"
                className="ia-btn-primary"
                disabled={!input.trim() || loading}
                onClick={() => void handleSend()}
              >
                <Send className="h-4 w-4" />
                发送
              </button>
            </div>
          </div>

          <details className="ia-advanced-drawer">
            <summary>分析视角（可选，最多 {MAX_SELECTED_SKILLS} 个）</summary>
            <div className="ia-advanced-body">
              {skills.length === 0 ? (
                <p>加载技能列表中…</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {skills.map((skill) => {
                    const selected = selectedSkillIds.includes(skill.id);
                    return (
                      <button
                        key={skill.id}
                        type="button"
                        title={skill.description}
                        className={`ia-chip ${selected ? 'ring-2 ring-[hsl(var(--primary))]' : ''}`}
                        onClick={() => toggleSkill(skill.id)}
                      >
                        {skill.displayName}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          </details>
        </div>
      </div>
    </div>
  );
};

export default CsChatPage;
