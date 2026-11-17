/**
 * 问数会话状态
 * 统一封装 SSE 流式问数、会话列表、历史会话加载、删除和长期记忆查询。
 */
import { computed, onBeforeUnmount, ref } from "vue";

import { streamQuery } from "../lib/agentApi";
import { summarizeResult } from "../lib/format";
import {
  deleteSession as deleteSessionApi,
  getSession,
  listMemories,
  listSessions,
} from "../lib/sessionsApi";
import type {
  AgentEvent,
  ChatMessage,
  MemoryItem,
  Notice,
  NoticeType,
  ProgressEvent,
  ServiceState,
  SessionInfo,
  SessionMessage,
} from "../types/agent";

const USER_ID = "default";

function makeId() {
  return (
    crypto.randomUUID?.() ??
    `${Date.now()}-${Math.random().toString(16).slice(2)}`
  );
}

function parseTime(value: string) {
  const timestamp = Date.parse(value);
  return Number.isNaN(timestamp) ? Date.now() : timestamp;
}

function toChatMessage(message: SessionMessage): ChatMessage {
  return {
    id: message.id,
    role: message.role,
    content: message.content,
    createdAt: parseTime(message.created_at),
    status: "done",
    steps: [],
    sql: message.sql || undefined,
    resolvedQuery: message.resolved_query || undefined,
    fromHistory: true,
  };
}

function upsertStep(message: ChatMessage, event: ProgressEvent) {
  const steps = message.steps ?? (message.steps = []);
  const index = steps.findIndex((step) => step.step === event.step);
  const nextStep = {
    step: event.step,
    status: event.status,
    updatedAt: Date.now(),
  };

  if (index >= 0) {
    steps[index] = { ...steps[index], ...nextStep };
  } else {
    steps.push(nextStep);
  }
}

function settleRunningSteps(message: ChatMessage) {
  message.steps = (message.steps ?? []).map((step) =>
    step.status === "running" ? { ...step, status: "error" as const } : step,
  );
}

export function useChat() {
  const messages = ref<ChatMessage[]>([]);
  const draft = ref("");
  const sessionId = ref<string | null>(null);
  const sessions = ref<SessionInfo[]>([]);
  const memories = ref<MemoryItem[]>([]);
  const isStreaming = ref(false);
  const memoryLoading = ref(false);
  const sessionsLoading = ref(false);
  const sessionsError = ref(false);
  const serviceState = ref<ServiceState>("ready");
  const notice = ref<Notice | null>(null);

  let controller: AbortController | null = null;
  let noticeTimer: ReturnType<typeof setTimeout> | undefined;

  const activeSession = computed(
    () =>
      sessions.value.find((item) => item.session_id === sessionId.value) ??
      null,
  );

  function clearNotice() {
    if (noticeTimer) clearTimeout(noticeTimer);
    notice.value = null;
  }

  function pushNotice(type: NoticeType, message: string) {
    if (noticeTimer) clearTimeout(noticeTimer);
    notice.value = { id: Date.now(), type, message };
    noticeTimer = setTimeout(() => {
      notice.value = null;
    }, 3600);
  }

  async function refreshSessions(silent = true) {
    sessionsLoading.value = true;
    sessionsError.value = false;
    try {
      sessions.value = await listSessions(USER_ID, 30);
      if (!isStreaming.value) serviceState.value = "ready";
    } catch (error) {
      sessionsError.value = true;
      if (!isStreaming.value) serviceState.value = "error";
      if (!silent) {
        pushNotice(
          "error",
          error instanceof Error ? error.message : "会话列表加载失败",
        );
      }
    } finally {
      sessionsLoading.value = false;
    }
  }

  async function startQuery(rawQuery?: string) {
    const query = (rawQuery ?? draft.value).trim();
    if (!query || isStreaming.value) return;

    draft.value = "";

    const userMessage: ChatMessage = {
      id: makeId(),
      role: "user",
      content: query,
      createdAt: Date.now(),
    };

    const assistantId = makeId();
    const assistantMessage: ChatMessage = {
      id: assistantId,
      role: "assistant",
      content: "正在理解你的问题…",
      createdAt: Date.now(),
      status: "streaming",
      steps: [],
    };

    messages.value.push(userMessage, assistantMessage);

    controller = new AbortController();
    isStreaming.value = true;
    serviceState.value = "busy";

    const currentAssistant = () =>
      messages.value.find((message) => message.id === assistantId);

    const onEvent = (event: AgentEvent) => {
      if (event.type === "session") {
        sessionId.value = event.session_id;
        return;
      }

      const message = currentAssistant();
      if (!message) return;

      if (event.type === "progress") {
        upsertStep(message, event);
        if (message.status === "streaming") {
          const running = [...(message.steps ?? [])]
            .reverse()
            .find((step) => step.status === "running");
          message.content = running ? `正在${running.step}…` : "正在整理分析结果…";
        }
        return;
      }

      if (event.type === "result") {
        message.status = "done";
        message.result = event.data;
        message.content = summarizeResult(event.data);
        return;
      }

      if (event.type === "error") {
        settleRunningSteps(message);
        message.status = "error";
        message.content = "这次分析没有完成。";
        message.error = event.message;
      }
    };

    try {
      await streamQuery(query, {
        signal: controller.signal,
        sessionId: sessionId.value ?? undefined,
        userId: USER_ID,
        onEvent,
      });

      const message = currentAssistant();
      if (message && message.status === "streaming") {
        settleRunningSteps(message);
        message.status = "done";
        message.content = "分析已结束，后端未返回查询结果。";
      }
    } catch (error) {
      const message = currentAssistant();
      const isAbort =
        error instanceof DOMException && error.name === "AbortError";

      if (message) {
        if (isAbort) {
          settleRunningSteps(message);
          message.status = "done";
          message.content = "已停止本次分析。";
        } else {
          settleRunningSteps(message);
          message.status = "error";
          message.content = "无法连接问数服务。";
          message.error =
            error instanceof Error ? error.message : String(error);
        }
      }

      if (!isAbort) {
        serviceState.value = "error";
        pushNotice("error", "请求失败，请确认后端服务已启动。");
      }
    } finally {
      isStreaming.value = false;
      controller = null;
      if (serviceState.value !== "error") serviceState.value = "ready";
      await refreshSessions(true);
    }
  }

  function stopQuery() {
    controller?.abort();
  }

  function newChat() {
    if (isStreaming.value) return;
    messages.value = [];
    draft.value = "";
    sessionId.value = null;
    memories.value = [];
  }

  async function selectSession(targetSessionId: string) {
    if (isStreaming.value || targetSessionId === sessionId.value) return;
    try {
      const detail = await getSession(targetSessionId);
      sessionId.value = detail.session_id;
      messages.value = detail.messages.map(toChatMessage);
      memories.value = [];
      serviceState.value = "ready";
    } catch (error) {
      serviceState.value = "error";
      pushNotice(
        "error",
        error instanceof Error ? error.message : "会话加载失败",
      );
    }
  }

  async function deleteSessionById(targetSessionId: string) {
    try {
      await deleteSessionApi(targetSessionId);
      sessions.value = sessions.value.filter(
        (session) => session.session_id !== targetSessionId,
      );
      if (sessionId.value === targetSessionId) {
        messages.value = [];
        sessionId.value = null;
        memories.value = [];
      }
      pushNotice("success", "会话已删除");
      return true;
    } catch (error) {
      pushNotice(
        "error",
        error instanceof Error ? error.message : "会话删除失败",
      );
      return false;
    }
  }

  async function loadMemories() {
    if (!sessionId.value) {
      pushNotice("info", "先进行一次问数，才能查看当前会话记忆");
      return;
    }

    memoryLoading.value = true;
    try {
      memories.value = await listMemories(sessionId.value, 100);
    } catch (error) {
      pushNotice(
        "error",
        error instanceof Error ? error.message : "长期记忆加载失败",
      );
    } finally {
      memoryLoading.value = false;
    }
  }

  onBeforeUnmount(() => {
    controller?.abort();
    if (noticeTimer) clearTimeout(noticeTimer);
  });

  return {
    userId: USER_ID,
    messages,
    draft,
    sessionId,
    sessions,
    memories,
    isStreaming,
    memoryLoading,
    sessionsLoading,
    sessionsError,
    serviceState,
    notice,
    activeSession,
    startQuery,
    stopQuery,
    newChat,
    selectSession,
    deleteSessionById,
    refreshSessions,
    loadMemories,
    pushNotice,
    clearNotice,
  };
}
