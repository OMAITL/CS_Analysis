import { create } from 'zustand';
import { csApi } from '../api/cs';
import type { CsChatSessionItem, CsChatStreamRequest } from '../api/cs';
import {
  getParsedApiError,
  isApiRequestError,
  isParsedApiError,
  type ParsedApiError,
} from '../api/error';
import { generateUUID } from '../utils/uuid';

const STORAGE_KEY_SESSION = 'dsa_cs_chat_session_id';

export interface ProgressStep {
  type: string;
  message?: string;
  content?: string;
  tool?: string;
  display_name?: string;
  duration?: number;
}

export interface CsChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  skills?: string[];
  skillNames?: string[];
  thinkingSteps?: ProgressStep[];
}

export interface StreamMeta {
  skillNames?: string[];
}

type StreamFailureEvent = {
  type: string;
  success?: boolean;
  content?: string;
  error?: unknown;
  message?: unknown;
};

function getStreamFailureError(event: StreamFailureEvent, fallbackMessage: string): ParsedApiError {
  const candidate = event.error ?? event.message ?? event.content ?? fallbackMessage;
  return getParsedApiError(typeof candidate === 'string' && candidate.trim() ? candidate : fallbackMessage);
}

interface CsChatState {
  messages: CsChatMessage[];
  loading: boolean;
  progressSteps: ProgressStep[];
  sessionId: string;
  sessions: CsChatSessionItem[];
  sessionsLoading: boolean;
  chatError: ParsedApiError | null;
  currentRoute: string;
  completionBadge: boolean;
  hasInitialLoad: boolean;
  abortController: AbortController | null;
}

interface CsChatActions {
  setCurrentRoute: (path: string) => void;
  clearCompletionBadge: () => void;
  loadSessions: () => Promise<void>;
  loadInitialSession: () => Promise<void>;
  switchSession: (targetSessionId: string) => Promise<void>;
  startNewChat: () => void;
  startStream: (payload: CsChatStreamRequest, meta?: StreamMeta) => Promise<void>;
}

const getInitialSessionId = (): string => {
  if (typeof localStorage === 'undefined') {
    return `cs_${generateUUID()}`;
  }
  const saved = localStorage.getItem(STORAGE_KEY_SESSION);
  if (saved?.trim()) {
    return saved.startsWith('cs_') ? saved : `cs_${saved}`;
  }
  const id = `cs_${generateUUID()}`;
  localStorage.setItem(STORAGE_KEY_SESSION, id);
  return id;
};

export const useCsChatStore = create<CsChatState & CsChatActions>((set, get) => ({
  messages: [],
  loading: false,
  progressSteps: [],
  sessionId: getInitialSessionId(),
  sessions: [],
  sessionsLoading: false,
  chatError: null,
  currentRoute: '',
  completionBadge: false,
  hasInitialLoad: false,
  abortController: null,

  setCurrentRoute: (path) => set({ currentRoute: path }),

  clearCompletionBadge: () => set({ completionBadge: false }),

  loadSessions: async () => {
    set({ sessionsLoading: true });
    try {
      const sessions = await csApi.getChatSessions();
      set({ sessions });
    } catch {
      // ignore
    } finally {
      set({ sessionsLoading: false });
    }
  },

  loadInitialSession: async () => {
    if (get().hasInitialLoad) return;
    set({ hasInitialLoad: true, sessionsLoading: true });
    try {
      const sessionList = await csApi.getChatSessions();
      set({ sessions: sessionList });
      const savedId = localStorage.getItem(STORAGE_KEY_SESSION);
      if (savedId) {
        const normalized = savedId.startsWith('cs_') ? savedId : `cs_${savedId}`;
        const exists = sessionList.some((s) => s.session_id === normalized);
        if (exists) {
          const msgs = await csApi.getChatSessionMessages(normalized);
          if (msgs.length > 0) {
            set({
              sessionId: normalized,
              messages: msgs.map((m) => ({
                id: m.id,
                role: m.role,
                content: m.content,
              })),
            });
          }
        } else {
          const newId = `cs_${generateUUID()}`;
          set({ sessionId: newId });
          localStorage.setItem(STORAGE_KEY_SESSION, newId);
        }
      } else {
        localStorage.setItem(STORAGE_KEY_SESSION, get().sessionId);
      }
    } catch {
      // ignore
    } finally {
      set({ sessionsLoading: false });
    }
  },

  switchSession: async (targetSessionId) => {
    const { sessionId, messages, abortController } = get();
    if (targetSessionId === sessionId && messages.length > 0) return;
    abortController?.abort();
    set({
      messages: [],
      sessionId: targetSessionId,
      loading: false,
      progressSteps: [],
      chatError: null,
      abortController: null,
    });
    localStorage.setItem(STORAGE_KEY_SESSION, targetSessionId);
    try {
      const msgs = await csApi.getChatSessionMessages(targetSessionId);
      if (get().sessionId !== targetSessionId) return;
      set({
        messages: msgs.map((m) => ({
          id: m.id,
          role: m.role,
          content: m.content,
        })),
      });
    } catch {
      // ignore
    }
  },

  startNewChat: () => {
    get().abortController?.abort();
    const newId = `cs_${generateUUID()}`;
    set({
      sessionId: newId,
      messages: [],
      loading: false,
      progressSteps: [],
      chatError: null,
      abortController: null,
    });
    localStorage.setItem(STORAGE_KEY_SESSION, newId);
  },

  startStream: async (payload, meta) => {
    if (get().loading) return;
    get().abortController?.abort();
    const ac = new AbortController();
    set({ abortController: ac });

    const streamSessionId = payload.session_id || get().sessionId;
    const skillNames = meta?.skillNames?.length ? meta.skillNames : ['通用'];

    const userMessage: CsChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: payload.message,
      skills: payload.skills,
      skillNames,
    };

    set((s) => ({
      messages: [...s.messages, userMessage],
      loading: true,
      progressSteps: [],
      chatError: null,
      sessions: s.sessions.some((x) => x.session_id === streamSessionId)
        ? s.sessions
        : [
            {
              session_id: streamSessionId,
              title: payload.message.slice(0, 60),
              message_count: 1,
              created_at: new Date().toISOString(),
              last_active: new Date().toISOString(),
            },
            ...s.sessions,
          ],
    }));

    try {
      const response = await csApi.chatStream({ ...payload, session_id: streamSessionId }, { signal: ac.signal });
      const reader = response.body!.getReader();
      const decoder = new TextDecoder();
      let buf = '';
      let finalContent: string | null = null;
      const currentProgressSteps: ProgressStep[] = [];

      const processLine = (line: string) => {
        if (!line.startsWith('data: ')) return;
        const event = JSON.parse(line.slice(6)) as ProgressStep & StreamFailureEvent;
        if (event.type === 'done') {
          if (event.success === false) {
            throw getStreamFailureError(event, '大模型调用出错，请检查 API Key 配置');
          }
          finalContent = event.content ?? '';
          return;
        }
        if (event.type === 'error') {
          throw getStreamFailureError(event, '回答出错');
        }
        currentProgressSteps.push(event);
        set((s) => ({ progressSteps: [...s.progressSteps, event] }));
      };

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        const lines = buf.split('\n');
        buf = lines.pop() ?? '';
        for (const line of lines) {
          try {
            processLine(line);
          } catch (parseErr: unknown) {
            if (isParsedApiError(parseErr) || isApiRequestError(parseErr)) {
              throw parseErr;
            }
          }
        }
      }

      if (buf.trim().startsWith('data: ')) {
        processLine(buf.trim());
      }

      const shouldAppend = get().sessionId === streamSessionId && !ac.signal.aborted;
      if (shouldAppend) {
        set((s) => ({
          messages: [
            ...s.messages,
            {
              id: (Date.now() + 1).toString(),
              role: 'assistant',
              content: finalContent || '（无内容）',
              skills: payload.skills,
              skillNames,
              thinkingSteps: [...currentProgressSteps],
            },
          ],
        }));
      }

      if (get().currentRoute !== '/chat') {
        set({ completionBadge: true });
      }
    } catch (error: unknown) {
      if (!(error instanceof Error && error.name === 'AbortError')) {
        set({ chatError: getParsedApiError(error) });
        if (get().currentRoute !== '/chat') {
          set({ completionBadge: true });
        }
      }
    } finally {
      if (get().abortController === ac) {
        set({ loading: false, progressSteps: [], abortController: null });
      }
      await get().loadSessions();
    }
  },
}));
