/**
 * 登录 Token 本地存储
 * Token 存在 localStorage，刷新页面后通过 /api/auth/me 恢复用户信息。
 */

const TOKEN_KEY = "nl2sql_access_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}
