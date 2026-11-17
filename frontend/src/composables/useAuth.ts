/**
 * 登录状态
 * 使用模块级单例，让登录页和主应用共享同一份用户状态。
 */
import { computed, ref } from "vue";

import {
  fetchMe,
  login as loginApi,
  register as registerApi,
} from "../lib/authApi";
import { clearToken, getToken, setToken } from "../lib/authStorage";
import type {
  AuthTokenResponse,
  AuthUser,
  LoginPayload,
  RegisterPayload,
} from "../types/auth";

const user = ref<AuthUser | null>(null);
const token = ref<string | null>(getToken());
const initialized = ref(false);
const authenticating = ref(false);
const authError = ref("");

function applySession(response: AuthTokenResponse) {
  setToken(response.access_token);
  token.value = response.access_token;
  user.value = response.user;
  authError.value = "";
}

function clearSession() {
  clearToken();
  token.value = null;
  user.value = null;
}

export function useAuth() {
  const isAuthenticated = computed(() => Boolean(user.value && token.value));

  async function initialize() {
    if (initialized.value) return;

    if (token.value) {
      try {
        user.value = await fetchMe();
      } catch {
        clearSession();
        authError.value = "登录状态已失效，请重新登录";
      }
    }
    initialized.value = true;
  }

  async function login(payload: LoginPayload): Promise<boolean> {
    authenticating.value = true;
    authError.value = "";
    try {
      applySession(await loginApi(payload));
      return true;
    } catch (error) {
      authError.value = error instanceof Error ? error.message : "登录失败";
      return false;
    } finally {
      authenticating.value = false;
    }
  }

  async function register(payload: RegisterPayload): Promise<boolean> {
    authenticating.value = true;
    authError.value = "";
    try {
      applySession(await registerApi(payload));
      return true;
    } catch (error) {
      authError.value = error instanceof Error ? error.message : "注册失败";
      return false;
    } finally {
      authenticating.value = false;
    }
  }

  function logout() {
    clearSession();
    authError.value = "";
  }

  function expire() {
    clearSession();
    authError.value = "登录已过期，请重新登录";
  }

  function clearAuthError() {
    authError.value = "";
  }

  return {
    user,
    token,
    isAuthenticated,
    initialized,
    authenticating,
    authError,
    initialize,
    login,
    register,
    logout,
    expire,
    clearAuthError,
  };
}
