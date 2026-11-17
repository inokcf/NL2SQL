/**
 * 会话管理接口客户端
 * 对接后端的会话列表、会话详情、删除会话和长期记忆查询接口。
 */
import { apiUrl, readErrorMessage } from "./apiBase";
import type {
  MemoryItem,
  SessionDetail,
  SessionInfo,
} from "../types/agent";

export async function listSessions(
  userId = "default",
  limit = 30,
): Promise<SessionInfo[]> {
  const params = new URLSearchParams({
    user_id: userId,
    limit: String(limit),
  });
  const response = await fetch(apiUrl(`/api/sessions?${params.toString()}`));
  if (!response.ok) throw new Error(await readErrorMessage(response));
  return (await response.json()) as SessionInfo[];
}

export async function getSession(sessionId: string): Promise<SessionDetail> {
  const response = await fetch(apiUrl(`/api/sessions/${sessionId}`));
  if (!response.ok) throw new Error(await readErrorMessage(response));
  return (await response.json()) as SessionDetail;
}

export async function deleteSession(sessionId: string): Promise<void> {
  const response = await fetch(apiUrl(`/api/sessions/${sessionId}`), {
    method: "DELETE",
  });
  if (!response.ok) throw new Error(await readErrorMessage(response));
}

export async function listMemories(
  sessionId: string,
  limit = 100,
): Promise<MemoryItem[]> {
  const params = new URLSearchParams({ limit: String(limit) });
  const response = await fetch(
    apiUrl(`/api/sessions/${sessionId}/memories?${params.toString()}`),
  );
  if (!response.ok) throw new Error(await readErrorMessage(response));
  return (await response.json()) as MemoryItem[];
}
