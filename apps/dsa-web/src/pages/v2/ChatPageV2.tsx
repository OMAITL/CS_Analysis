import type React from 'react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Send } from 'lucide-react';
import { agentApi } from '../../api/agent';
import type { SkillInfo } from '../../api/agent';
import { ApiErrorAlert } from '../../components/common';
import { useAgentChatStore } from '../../stores/agentChatStore';
import '../../styles/ia-v2.css';

const CS_QUICK_QUESTIONS = [
  { label: '这个饰品能买吗？', skill: 'bull_trend' },
  { label: '未来一周怎么看？', skill: 'box_oscillation' },
  { label: '帮我找低风险标的', skill: 'bull_trend' },
  { label: '最近哪些饰品热度上涨？', skill: 'emotion_cycle' },
];

const MAX_SELECTED_SKILLS = 3;

const ChatPageV2: React.FC = () => {
  const [input, setInput] = useState('');
  const [skills, setSkills] = useState<SkillInfo[]>([]);
  const [selectedSkillIds, setSelectedSkillIds] = useState<string[]>([]);

  const messages = useAgentChatStore((s) => s.messages);
  const loading = useAgentChatStore((s) => s.loading);
  const sessionId = useAgentChatStore((s) => s.sessionId);
  const chatError = useAgentChatStore((s) => s.chatError);
  const startStream = useAgentChatStore((s) => s.startStream);
  const startNewChat = useAgentChatStore((s) => s.startNewChat);
  const loadInitialSession = useAgentChatStore((s) => s.loadInitialSession);

  useEffect(() => {
    document.title = '问股预览 - DSA';
    void loadInitialSession();
  }, [loadInitialSession]);

  useEffect(() => {
    let active = true;
    agentApi
      .getSkills()
      .then((res) => {
        if (active) {
          setSkills(res.skills);
        }
      })
      .catch(() => {
        if (active) {
          setSkills([]);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  const availableSkillIds = useMemo(() => new Set(skills.map((s) => s.id)), [skills]);

  const quickQuestions = useMemo(
    () =>
      CS_QUICK_QUESTIONS.filter(
        (q) => availableSkillIds.size === 0 || availableSkillIds.has(q.skill),
      ),
    [availableSkillIds],
  );

  const getSkillNames = useCallback(
    (skillIds: string[]) => skillIds.map((id) => skills.find((s) => s.id === id)?.name || id),
    [skills],
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
    async (overrideMessage?: string, overrideSkillIds?: string[]) => {
      const msgText = (overrideMessage ?? input).trim();
      if (!msgText || loading) {
        return;
      }
      const usedSkillIds = normalizeSelectedSkillIds(overrideSkillIds ?? selectedSkillIds);
      const usedSkillNames =
        usedSkillIds.length > 0 ? getSkillNames(usedSkillIds) : ['通用'];

      setInput('');
      await startStream(
        {
          message: msgText,
          session_id: sessionId,
          ...(usedSkillIds.length > 0 ? { skills: usedSkillIds } : {}),
        },
        {
          skillNames: usedSkillNames,
          skillName: usedSkillNames.join('、'),
        },
      );
    },
    [
      getSkillNames,
      input,
      loading,
      normalizeSelectedSkillIds,
      selectedSkillIds,
      sessionId,
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
      if (prev.includes(skillId)) {
        return prev.filter((id) => id !== skillId);
      }
      if (prev.length >= MAX_SELECTED_SKILLS) {
        return prev;
      }
      return [...prev, skillId];
    });
  };

  const hasMessages = messages.length > 0;

  return (
    <div className="ia-v2-root flex min-h-0 flex-1 flex-col">
      <div className="ia-preview-banner">
        <span>问股 UI 预览版</span>
        <Link to="/chat">返回正式问股</Link>
        <span className="ia-muted">·</span>
        <Link to="/">饰品分析</Link>
      </div>

      <div className="ia-chat-v2">
        {chatError ? (
          <div className="mb-3">
            <ApiErrorAlert error={chatError} />
          </div>
        ) : null}

        {!hasMessages ? (
          <div className="ia-chat-hero">
            <h1>对话式问股 Agent</h1>
            <p className="ia-muted text-sm">
              自由提问、多轮对话；需要结构化饰品分析请使用
              {' '}
              <Link to="/" className="ia-link">饰品 Agent 工作台</Link>
            </p>
          </div>
        ) : null}

        <div className="ia-chat-messages">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`ia-chat-bubble ${
                msg.role === 'user' ? 'ia-chat-bubble-user' : 'ia-chat-bubble-assistant'
              }`}
            >
              {msg.content || (loading && msg.role === 'assistant' ? '思考中…' : '')}
            </div>
          ))}
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
                  void handleSend(q.label, [q.skill]);
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
            placeholder="输入你的问题，例如：蝴蝶刀现在适合入手吗？"
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
          <summary>高级分析</summary>
          <div className="ia-advanced-body">
            <p className="mb-2">可选策略（最多 {MAX_SELECTED_SKILLS} 个）：</p>
            {skills.length === 0 ? (
              <p>加载策略列表中…</p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {skills.map((skill) => {
                  const selected = selectedSkillIds.includes(skill.id);
                  return (
                    <button
                      key={skill.id}
                      type="button"
                      className={`ia-chip ${selected ? 'ring-2 ring-[hsl(var(--primary))]' : ''}`}
                      onClick={() => toggleSkill(skill.id)}
                    >
                      {skill.name}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </details>
      </div>
    </div>
  );
};

export default ChatPageV2;
