/**
 * 认证相关类型
 * 与后端 /api/auth 接口保持一致。
 */

export type AuthUser = {
  id: string;
  username: string;
  display_name: string;
  role: string;
  created_at: string;
};

export type LoginPayload = {
  username: string;
  password: string;
};

export type RegisterPayload = {
  username: string;
  password: string;
  display_name?: string;
};

export type AuthTokenResponse = {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: AuthUser;
};
