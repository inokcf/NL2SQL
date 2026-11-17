/**
 * 认证接口客户端
 * 封装注册、登录和当前用户查询。
 */
import { apiUrl, authHeaders, readErrorMessage } from "./apiBase";
import type {
  AuthTokenResponse,
  AuthUser,
  LoginPayload,
  RegisterPayload,
} from "../types/auth";

async function parseTokenResponse(
  response: Response,
): Promise<AuthTokenResponse> {
  if (!response.ok) throw new Error(await readErrorMessage(response));
  return (await response.json()) as AuthTokenResponse;
}

export async function login(
  payload: LoginPayload,
): Promise<AuthTokenResponse> {
  const response = await fetch(apiUrl("/api/auth/login"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseTokenResponse(response);
}

export async function register(
  payload: RegisterPayload,
): Promise<AuthTokenResponse> {
  const response = await fetch(apiUrl("/api/auth/register"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseTokenResponse(response);
}

export async function fetchMe(): Promise<AuthUser> {
  const response = await fetch(apiUrl("/api/auth/me"), {
    headers: authHeaders(),
  });
  if (!response.ok) throw new Error(await readErrorMessage(response));
  return (await response.json()) as AuthUser;
}
