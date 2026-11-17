<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import {
  AlertCircle,
  Brain,
  Database,
  Eye,
  EyeOff,
  LoaderCircle,
  ShieldCheck,
  Sparkles,
} from "lucide-vue-next";

import { useAuth } from "../composables/useAuth";

const {
  authenticating,
  authError,
  login,
  register,
  clearAuthError,
} = useAuth();

const mode = ref<"login" | "register">("login");
const username = ref("");
const password = ref("");
const displayName = ref("");
const showPassword = ref(false);
const localError = ref("");
const usernameInput = ref<HTMLInputElement | null>(null);

const errorMessage = computed(() => localError.value || authError.value);

const title = computed(() =>
  mode.value === "login" ? "欢迎回来" : "创建你的账号",
);

const subtitle = computed(() =>
  mode.value === "login"
    ? "登录后继续你的多轮问数与分析记忆"
    : "注册后即可拥有独立的会话与长期记忆空间",
);

const submitLabel = computed(() =>
  mode.value === "login" ? "登录" : "注册并登录",
);

watch([username, password, displayName], () => {
  if (localError.value) localError.value = "";
});

onMounted(() => {
  usernameInput.value?.focus();
});

function switchMode(next: "login" | "register") {
  mode.value = next;
  localError.value = "";
  clearAuthError();
}

function fillDemo() {
  mode.value = "login";
  username.value = "admin";
  password.value = "admin123";
  localError.value = "";
  clearAuthError();
  usernameInput.value?.focus();
}

async function submit() {
  localError.value = "";
  const name = username.value.trim();
  const pwd = password.value;

  if (!name) {
    localError.value = "请输入用户名";
    return;
  }
  if (mode.value === "register" && name.length < 3) {
    localError.value = "用户名至少需要 3 个字符";
    return;
  }
  if (!pwd) {
    localError.value = "请输入密码";
    return;
  }
  if (mode.value === "register" && pwd.length < 6) {
    localError.value = "密码至少需要 6 个字符";
    return;
  }

  const ok =
    mode.value === "login"
      ? await login({ username: name, password: pwd })
      : await register({
          username: name,
          password: pwd,
          display_name: displayName.value.trim() || undefined,
        });

  if (ok) password.value = "";
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-glow auth-glow--mint" aria-hidden="true" />
    <div class="auth-glow auth-glow--sky" aria-hidden="true" />

    <div class="auth-panel">
      <aside class="brand-panel">
        <div class="brand-row">
          <span class="brand-logo" aria-hidden="true">
            <Sparkles :size="21" />
          </span>
          <div class="brand-copy">
            <strong>AI问数</strong>
            <span>NL2SQL Agent</span>
          </div>
        </div>

        <div class="brand-hero">
          <span class="brand-eyebrow">自然语言数据分析</span>
          <h1>
            让数据<br />
            <span>直接回答</span>你的问题
          </h1>
          <p>
            用一句话完成字段召回、指标理解与 SQL 生成。
            登录后，会话与长期偏好都会按用户独立保存。
          </p>
        </div>

        <ul class="feature-list">
          <li>
            <span class="feature-icon"><Brain :size="16" /></span>
            <div>
              <strong>多轮记忆</strong>
              <span>自动理解追问与历史偏好</span>
            </div>
          </li>
          <li>
            <span class="feature-icon"><ShieldCheck :size="16" /></span>
            <div>
              <strong>用户级隔离</strong>
              <span>会话与向量记忆按账号隔离</span>
            </div>
          </li>
          <li>
            <span class="feature-icon"><Database :size="16" /></span>
            <div>
              <strong>混合检索与 SQL 闭环</strong>
              <span>从自然语言到可执行查询</span>
            </div>
          </li>
        </ul>

        <p class="brand-foot">Redis · Qdrant · LangGraph · FastAPI</p>
      </aside>

      <main class="form-panel">
        <div class="form-card">
          <div class="mobile-brand">
            <span class="brand-logo small" aria-hidden="true">
              <Sparkles :size="18" />
            </span>
            <div class="brand-copy">
              <strong>AI问数</strong>
              <span>NL2SQL Agent</span>
            </div>
          </div>

          <div class="mode-tabs" role="tablist" aria-label="登录或注册">
            <button
              type="button"
              role="tab"
              :aria-selected="mode === 'login'"
              :class="{ active: mode === 'login' }"
              @click="switchMode('login')"
            >
              登录
            </button>
            <button
              type="button"
              role="tab"
              :aria-selected="mode === 'register'"
              :class="{ active: mode === 'register' }"
              @click="switchMode('register')"
            >
              注册
            </button>
          </div>

          <header class="form-head">
            <h2>{{ title }}</h2>
            <p>{{ subtitle }}</p>
          </header>

          <form @submit.prevent="submit">
            <label class="field">
              <span>用户名</span>
              <input
                ref="usernameInput"
                v-model="username"
                type="text"
                autocomplete="username"
                maxlength="64"
                placeholder="请输入用户名"
              />
            </label>

            <label v-if="mode === 'register'" class="field">
              <span>显示名称 <em>选填</em></span>
              <input
                v-model="displayName"
                type="text"
                autocomplete="nickname"
                maxlength="64"
                placeholder="例如：数据分析师"
              />
            </label>

            <label class="field">
              <span>密码</span>
              <span class="password-field">
                <input
                  v-model="password"
                  :type="showPassword ? 'text' : 'password'"
                  :autocomplete="
                    mode === 'login' ? 'current-password' : 'new-password'
                  "
                  maxlength="128"
                  placeholder="请输入密码"
                />
                <button
                  type="button"
                  class="password-toggle"
                  :aria-label="showPassword ? '隐藏密码' : '显示密码'"
                  @click="showPassword = !showPassword"
                >
                  <EyeOff v-if="showPassword" :size="15" />
                  <Eye v-else :size="15" />
                </button>
              </span>
            </label>

            <p v-if="errorMessage" class="form-error" role="alert">
              <AlertCircle :size="15" />
              <span>{{ errorMessage }}</span>
            </p>

            <button
              type="submit"
              class="submit-button"
              :disabled="authenticating"
            >
              <LoaderCircle v-if="authenticating" class="spin" :size="16" />
              {{ authenticating ? "请稍候…" : submitLabel }}
            </button>
          </form>

          <div v-if="mode === 'login'" class="demo-card">
            <div class="demo-copy">
              <strong>体验账号</strong>
              <span><code>admin</code> / <code>admin123</code></span>
            </div>
            <button type="button" class="demo-fill" @click="fillDemo">
              填入
            </button>
          </div>

          <p class="switch-hint">
            {{ mode === "login" ? "还没有账号？" : "已经有账号？" }}
            <button
              type="button"
              @click="switchMode(mode === 'login' ? 'register' : 'login')"
            >
              {{ mode === "login" ? "立即注册" : "返回登录" }}
            </button>
          </p>
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  position: relative;
  display: grid;
  min-height: 100dvh;
  place-items: center;
  overflow: hidden;
  padding: 24px;
  background:
    radial-gradient(circle at 8% -8%, rgba(16, 156, 137, 0.13), transparent 34%),
    radial-gradient(circle at 96% 2%, rgba(77, 141, 247, 0.11), transparent 30%),
    var(--bg);
}

.auth-glow {
  position: absolute;
  border-radius: 999px;
  filter: blur(90px);
  pointer-events: none;
}

.auth-glow--mint {
  top: -120px;
  left: 10%;
  width: 420px;
  height: 420px;
  background: rgba(24, 183, 162, 0.16);
}

.auth-glow--sky {
  right: 5%;
  bottom: -160px;
  width: 480px;
  height: 480px;
  background: rgba(77, 141, 247, 0.12);
}

.auth-panel {
  position: relative;
  z-index: 1;
  display: grid;
  width: min(1120px, 100%);
  min-height: min(720px, calc(100dvh - 48px));
  grid-template-columns: 1.04fr 0.96fr;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.6);
  border-radius: 30px;
  background: var(--surface);
  box-shadow: var(--shadow-lg);
}

.brand-panel {
  position: relative;
  display: flex;
  min-width: 0;
  flex-direction: column;
  overflow: hidden;
  padding: 44px 46px 34px;
  background:
    radial-gradient(circle at 86% 12%, rgba(255, 255, 255, 0.2), transparent 28%),
    linear-gradient(150deg, #0a7b6d 0%, #0f9f8c 48%, #357fe5 125%);
  color: #fff;
}

.brand-panel::before,
.brand-panel::after {
  position: absolute;
  border-radius: 999px;
  content: "";
  pointer-events: none;
}

.brand-panel::before {
  top: -90px;
  right: -70px;
  width: 280px;
  height: 280px;
  background: rgba(255, 255, 255, 0.08);
}

.brand-panel::after {
  bottom: -120px;
  left: -80px;
  width: 320px;
  height: 320px;
  background: rgba(77, 141, 247, 0.22);
}

.brand-row,
.mobile-brand {
  display: flex;
  align-items: center;
  gap: 11px;
}

.brand-logo {
  display: grid;
  width: 42px;
  height: 42px;
  flex: 0 0 auto;
  place-items: center;
  border: 1px solid rgba(255, 255, 255, 0.28);
  border-radius: 13px;
  background: rgba(255, 255, 255, 0.16);
  backdrop-filter: blur(8px);
  color: #fff;
}

.brand-logo.small {
  width: 36px;
  height: 36px;
  border-color: rgba(16, 156, 137, 0.16);
  background: var(--brand-soft);
  color: var(--brand-deep);
}

.brand-copy {
  display: flex;
  min-width: 0;
  flex-direction: column;
  line-height: 1.3;
}

.brand-copy strong {
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.01em;
}

.brand-copy span {
  font-size: 10.5px;
  letter-spacing: 0.08em;
  opacity: 0.62;
}

.brand-hero {
  margin-top: auto;
  padding-top: 48px;
}

.brand-eyebrow {
  display: inline-block;
  margin-bottom: 14px;
  padding: 3px 9px;
  border: 1px solid rgba(255, 255, 255, 0.22);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.1);
  font-size: 9.5px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.brand-hero h1 {
  margin: 0;
  font-size: clamp(34px, 4vw, 46px);
  font-weight: 750;
  letter-spacing: -0.04em;
  line-height: 1.16;
}

.brand-hero h1 span {
  color: #c6fff4;
}

.brand-hero p {
  max-width: 390px;
  margin: 18px 0 0;
  color: rgba(255, 255, 255, 0.72);
  font-size: 12.5px;
  line-height: 1.85;
}

.feature-list {
  display: flex;
  flex-direction: column;
  gap: 9px;
  margin: 30px 0 0;
  padding: 0;
  list-style: none;
}

.feature-list li {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 11px;
  border: 1px solid rgba(255, 255, 255, 0.13);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(6px);
}

.feature-icon {
  display: grid;
  width: 30px;
  height: 30px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 9px;
  background: rgba(255, 255, 255, 0.14);
}

.feature-list li > div {
  display: flex;
  flex-direction: column;
  line-height: 1.35;
}

.feature-list strong {
  font-size: 11.5px;
  font-weight: 650;
}

.feature-list li span {
  color: rgba(255, 255, 255, 0.6);
  font-size: 10px;
}

.brand-foot {
  margin: auto 0 0;
  padding-top: 26px;
  color: rgba(255, 255, 255, 0.45);
  font-size: 9px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.form-panel {
  display: flex;
  min-width: 0;
  align-items: center;
  justify-content: center;
  padding: 42px 40px;
  background: var(--surface);
}

.form-card {
  width: 100%;
  max-width: 378px;
}

.mobile-brand {
  display: none;
  margin-bottom: 24px;
}

.mode-tabs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px;
  padding: 4px;
  border-radius: 12px;
  background: var(--surface-muted);
}

.mode-tabs button {
  height: 34px;
  border: 0;
  border-radius: 9px;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 12px;
  font-weight: 650;
  transition:
    background 160ms ease,
    color 160ms ease,
    box-shadow 160ms ease;
}

.mode-tabs button.active {
  background: var(--surface);
  box-shadow: var(--shadow-xs);
  color: var(--text);
}

.form-head {
  margin: 28px 0 22px;
}

.form-head h2 {
  margin: 0;
  color: var(--text);
  font-size: 25px;
  font-weight: 750;
  letter-spacing: -0.03em;
}

.form-head p {
  margin: 7px 0 0;
  color: var(--text-muted);
  font-size: 11.5px;
  line-height: 1.6;
}

form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field > span:first-child {
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: 650;
}

.field em {
  margin-left: 4px;
  color: var(--text-muted);
  font-size: 9.5px;
  font-style: normal;
  font-weight: 500;
}

.field input {
  width: 100%;
  height: 44px;
  padding: 0 12px;
  border: 1px solid var(--border);
  border-radius: 11px;
  background: var(--surface-soft);
  color: var(--text);
  font-size: 13px;
  outline: none;
  transition:
    border-color 160ms ease,
    background 160ms ease,
    box-shadow 160ms ease;
}

.field input::placeholder {
  color: var(--text-muted);
}

.field input:focus {
  border-color: rgba(16, 156, 137, 0.42);
  background: var(--surface);
  box-shadow: 0 0 0 4px rgba(16, 156, 137, 0.08);
}

.password-field {
  position: relative;
  display: block;
}

.password-field input {
  padding-right: 42px;
}

.password-toggle {
  position: absolute;
  top: 50%;
  right: 7px;
  display: grid;
  width: 30px;
  height: 30px;
  place-items: center;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  transform: translateY(-50%);
  transition:
    background 150ms ease,
    color 150ms ease;
}

.password-toggle:hover {
  background: var(--surface-muted);
  color: var(--text);
}

.form-error {
  display: flex;
  align-items: flex-start;
  gap: 7px;
  margin: 0;
  padding: 9px 11px;
  border: 1px solid rgba(217, 82, 82, 0.17);
  border-radius: 10px;
  background: var(--danger-soft);
  color: #b33f3f;
  font-size: 11px;
  line-height: 1.55;
}

.form-error svg {
  flex: 0 0 auto;
  margin-top: 1px;
}

.submit-button {
  display: inline-flex;
  width: 100%;
  height: 44px;
  align-items: center;
  justify-content: center;
  gap: 7px;
  margin-top: 4px;
  border: 0;
  border-radius: 12px;
  background: linear-gradient(135deg, #17ae99, #0b897a);
  box-shadow: 0 10px 22px rgba(16, 156, 137, 0.22);
  color: #fff;
  cursor: pointer;
  font-size: 13px;
  font-weight: 650;
  transition:
    transform 160ms ease,
    box-shadow 160ms ease,
    opacity 160ms ease;
}

.submit-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 14px 26px rgba(16, 156, 137, 0.28);
}

.submit-button:active:not(:disabled) {
  transform: translateY(0);
}

.submit-button:disabled {
  cursor: wait;
  opacity: 0.65;
}

.demo-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 18px;
  padding: 10px 12px;
  border: 1px dashed rgba(16, 156, 137, 0.22);
  border-radius: 11px;
  background: rgba(225, 245, 240, 0.5);
}

.demo-copy {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.demo-copy strong {
  color: var(--brand-deep);
  font-size: 10.5px;
  font-weight: 700;
}

.demo-copy span {
  color: var(--text-muted);
  font-size: 10.5px;
}

.demo-copy code {
  padding: 1px 5px;
  border-radius: 4px;
  background: var(--surface);
  color: var(--brand-deep);
  font-family: var(--font-mono);
  font-size: 10px;
}

.demo-fill {
  flex: 0 0 auto;
  padding: 4px 10px;
  border: 1px solid rgba(16, 156, 137, 0.2);
  border-radius: 7px;
  background: var(--surface);
  color: var(--brand-deep);
  cursor: pointer;
  font-size: 10px;
  font-weight: 650;
}

.demo-fill:hover {
  background: var(--brand-soft);
}

.switch-hint {
  margin: 20px 0 0;
  color: var(--text-muted);
  font-size: 10.5px;
  text-align: center;
}

.switch-hint button {
  border: 0;
  background: transparent;
  color: var(--brand-deep);
  cursor: pointer;
  font-size: 10.5px;
  font-weight: 650;
}

.switch-hint button:hover {
  text-decoration: underline;
}

@media (max-width: 900px) {
  .auth-panel {
    min-height: auto;
    grid-template-columns: 1fr;
  }

  .brand-panel {
    display: none;
  }

  .form-panel {
    padding: 38px 28px;
  }

  .mobile-brand {
    display: flex;
  }

  .mobile-brand .brand-copy span {
    color: var(--text-muted);
  }
}

@media (max-width: 600px) {
  .auth-page {
    padding: 0;
  }

  .auth-panel {
    min-height: 100dvh;
    border: 0;
    border-radius: 0;
  }

  .form-panel {
    padding: 30px 20px;
  }
}
</style>
