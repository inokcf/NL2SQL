/**
 * API 基址与通用请求工具
 * VITE_API_BASE_URL 为空时使用同源 /api，由 Vite 开发代理转发到 FastAPI。
 */

export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(
  /\/$/,
  "",
);

export function apiUrl(path: string) {
  return `${API_BASE_URL}${path}`;
}

export async function readErrorMessage(response: Response) {
  try {
    const payload = (await response.json()) as { detail?: string };
    if (payload?.detail) return payload.detail;
  } catch {
    // 响应不是 JSON 时退回 HTTP 状态码
  }
  return `接口请求失败：HTTP ${response.status}`;
}
