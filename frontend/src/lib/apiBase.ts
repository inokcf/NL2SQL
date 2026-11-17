/**
 * API 基址与通用请求工具
 * VITE_API_BASE_URL 为空时使用同源 /api，由 Vite 开发代理转发到 FastAPI。
 */
import { clearToken, getToken } from "./authStorage";

export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(
  /\/$/,
  "",
);

export const AUTH_EXPIRED_EVENT = "nl2sql:auth-expired";

export function apiUrl(path: string) {
  return `${API_BASE_URL}${path}`;
}

export function authHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export function handleUnauthorized(status: number) {
  if (status !== 401) return;
  clearToken();
  window.dispatchEvent(new Event(AUTH_EXPIRED_EVENT));
}

export async function readErrorMessage(response: Response) {
  try {
    const payload = (await response.json()) as {
      detail?: string | Array<{ msg?: string }>;
    };
    if (typeof payload?.detail === "string") return payload.detail;
    if (Array.isArray(payload?.detail)) {
      const messages = payload.detail
        .map((item) => item?.msg)
        .filter((message): message is string => Boolean(message));
      if (messages.length) return messages.join("；");
    }
  } catch {
    // 响应不是 JSON 时退回 HTTP 状态码
  }
  return `接口请求失败：HTTP ${response.status}`;
}
