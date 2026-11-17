/**
 * 智能体相关类型
 * 与后端 SSE 事件、Redis 会话接口和 Qdrant 长期记忆接口保持一致。
 */

export type ProgressStatus = "running" | "success" | "error";

export type ProgressEvent = {
  type: "progress";
  step: string;
  status: ProgressStatus;
};

export type ResultEvent = {
  type: "result";
  data: unknown;
};

export type ErrorEvent = {
  type: "error";
  message: string;
};

export type SessionEvent = {
  type: "session";
  session_id: string;
  user_id: string;
};

export type AgentEvent = ProgressEvent | ResultEvent | ErrorEvent | SessionEvent;

export type StepState = {
  step: string;
  status: ProgressStatus;
  updatedAt: number;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt: number;
  status?: "streaming" | "done" | "error";
  steps?: StepState[];
  result?: unknown;
  error?: string;
  /** 会话详情中保存的 SQL，用于历史消息回看 */
  sql?: string;
  /** 多轮追问改写后的问题 */
  resolvedQuery?: string;
  /** 是否来自历史会话详情 */
  fromHistory?: boolean;
};

export type SessionInfo = {
  session_id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
};

export type SessionMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
  sql: string;
  resolved_query: string;
  metadata: Record<string, unknown>;
};

export type SessionDetail = SessionInfo & {
  messages: SessionMessage[];
};

export type MemoryItem = {
  id: string;
  user_id: string;
  session_id: string;
  memory_type: "episodic" | "semantic" | string;
  content: string;
  question: string;
  resolved_query: string;
  sql: string;
  created_at: string;
  score?: number | null;
};

export type ServiceState = "ready" | "busy" | "error";

export type NoticeType = "success" | "error" | "info";

export type Notice = {
  id: number;
  type: NoticeType;
  message: string;
};
