<script setup lang="ts">
import { computed } from "vue";
import {
  AlertCircle,
  Brain,
  History,
  LoaderCircle,
  LogOut,
  MessageSquare,
  Plus,
  RefreshCw,
  Sparkles,
  Trash2,
  X,
} from "lucide-vue-next";

import { relativeTime } from "../lib/format";
import type { ExamplePrompt } from "../lib/examples";
import type { ServiceState, SessionInfo } from "../types/agent";
import type { AuthUser } from "../types/auth";

const props = defineProps<{
  sessions: SessionInfo[];
  activeSessionId: string | null;
  isStreaming: boolean;
  sessionsLoading: boolean;
  sessionsError: boolean;
  serviceState: ServiceState;
  user: AuthUser | null;
  examples: ExamplePrompt[];
}>();

const emit = defineEmits<{
  (event: "new-chat"): void;
  (event: "select-session", sessionId: string): void;
  (event: "delete-session", session: SessionInfo): void;
  (event: "use-example", text: string): void;
  (event: "refresh"): void;
  (event: "close"): void;
  (event: "logout"): void;
}>();

const statusText = computed(() => {
  if (props.serviceState === "busy") return "正在分析";
  if (props.serviceState === "error") return "连接异常";
  return "服务就绪";
});

const statusClass = computed(() => `is-${props.serviceState}`);

const displayName = computed(
  () => props.user?.display_name || props.user?.username || "未登录",
);

const userMeta = computed(() => {
  if (!props.user) return "未登录";
  const role = props.user.role === "admin" ? "管理员" : "普通用户";
  return `@${props.user.username} · ${role}`;
});

const userInitial = computed(() =>
  (props.user?.display_name || props.user?.username || "U")
    .trim()
    .charAt(0)
    .toUpperCase(),
);
</script>

<template>
  <aside class="sidebar">
    <div class="sidebar-head">
      <div class="brand">
        <div class="brand-logo" aria-hidden="true">
          <Sparkles :size="20" />
        </div>
        <div class="brand-copy">
          <strong>AI问数</strong>
          <span>NL2SQL Agent</span>
        </div>
        <button
          type="button"
          class="icon-button sidebar-close"
          aria-label="收起侧边栏"
          @click="emit('close')"
        >
          <X :size="18" />
        </button>
      </div>

      <button
        type="button"
        class="new-chat"
        :disabled="isStreaming"
        @click="emit('new-chat')"
      >
        <Plus :size="17" />
        开始新对话
      </button>
    </div>

    <div class="sidebar-scroll">
      <section class="section">
        <div class="section-head">
          <span class="section-title">
            <History :size="14" />
            最近会话
          </span>
          <button
            type="button"
            class="icon-button refresh-button"
            title="刷新会话"
            aria-label="刷新会话"
            :disabled="sessionsLoading"
            @click="emit('refresh')"
          >
            <LoaderCircle v-if="sessionsLoading" class="spin" :size="14" />
            <RefreshCw v-else :size="14" />
          </button>
        </div>

        <div
          v-if="sessionsLoading && !sessions.length"
          class="empty-sessions is-loading"
        >
          <LoaderCircle class="spin" :size="18" />
          <p>正在加载会话…</p>
          <span>正在读取 Redis 短期记忆</span>
        </div>

        <div
          v-else-if="sessionsError && !sessions.length"
          class="empty-sessions is-error"
        >
          <AlertCircle :size="18" />
          <p>会话加载失败</p>
          <span>请确认后端服务正常运行</span>
          <button type="button" class="retry-button" @click="emit('refresh')">
            重新加载
          </button>
        </div>

        <div v-else-if="sessions.length" class="session-list">
          <div
            v-for="session in sessions"
            :key="session.session_id"
            class="session-item"
            :class="{
              'is-active': session.session_id === activeSessionId,
              'is-disabled': isStreaming,
            }"
          >
            <button
              type="button"
              class="session-main"
              :disabled="isStreaming"
              @click="emit('select-session', session.session_id)"
            >
              <span class="session-indicator" aria-hidden="true" />
              <span class="session-copy">
                <span class="session-title">{{ session.title || "未命名会话" }}</span>
                <span class="session-meta">
                  {{ relativeTime(session.updated_at) }} ·
                  {{ session.message_count }} 条消息
                </span>
              </span>
            </button>
            <button
              type="button"
              class="icon-button session-delete"
              title="删除会话"
              aria-label="删除会话"
              :disabled="isStreaming"
              @click.stop="emit('delete-session', session)"
            >
              <Trash2 :size="14" />
            </button>
          </div>
        </div>

        <div v-else class="empty-sessions">
          <MessageSquare :size="18" />
          <p>还没有会话</p>
          <span>问第一个问题，这里会自动留下记录</span>
        </div>
      </section>

      <section class="section">
        <div class="section-head">
          <span class="section-title">
            <Sparkles :size="14" />
            灵感样例
          </span>
        </div>
        <div class="example-list">
          <button
            v-for="example in examples"
            :key="example.text"
            type="button"
            class="example-item"
            :disabled="isStreaming"
            @click="emit('use-example', example.text)"
          >
            <span class="example-icon" aria-hidden="true">
              <component :is="example.icon" :size="15" />
            </span>
            <span class="example-copy">
              <span class="example-label">{{ example.label }}</span>
              <span class="example-text">{{ example.text }}</span>
            </span>
          </button>
        </div>
      </section>
    </div>

    <div class="sidebar-foot">
      <div class="service-card">
        <span class="service-dot" :class="statusClass" aria-hidden="true" />
        <div class="service-copy">
          <strong>{{ statusText }}</strong>
          <span>会话与记忆服务</span>
        </div>
        <Brain :size="16" class="service-icon" aria-hidden="true" />
      </div>

      <div class="user-card">
        <span class="user-avatar" aria-hidden="true">{{ userInitial }}</span>
        <div class="user-copy">
          <strong>{{ displayName }}</strong>
          <span>{{ userMeta }}</span>
        </div>
        <button
          type="button"
          class="icon-button logout-button"
          title="退出登录"
          aria-label="退出登录"
          @click="emit('logout')"
        >
          <LogOut :size="15" />
        </button>
      </div>

      <p class="foot-note">Redis 短期会话 · Qdrant 长期记忆</p>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  display: flex;
  width: 292px;
  min-width: 292px;
  height: 100dvh;
  flex-direction: column;
  border-right: 1px solid rgba(210, 226, 221, 0.75);
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(22px);
  -webkit-backdrop-filter: blur(22px);
}

.sidebar-head {
  padding: 22px 18px 16px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 0 4px;
}

.brand-logo {
  display: grid;
  width: 40px;
  height: 40px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 13px;
  background: linear-gradient(135deg, #18b7a2, #0b8b79);
  box-shadow: 0 8px 18px rgba(16, 156, 137, 0.24);
  color: #fff;
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
  color: var(--text-muted);
  font-size: 11px;
  letter-spacing: 0.06em;
}

.sidebar-close {
  display: none;
  margin-left: auto;
}

.new-chat {
  display: flex;
  width: 100%;
  height: 44px;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 18px;
  border: 0;
  border-radius: 13px;
  background: linear-gradient(135deg, #13a994, #0b897a);
  box-shadow: 0 10px 22px rgba(16, 156, 137, 0.2);
  color: #fff;
  cursor: pointer;
  font-size: 14px;
  font-weight: 650;
  transition:
    transform 160ms ease,
    box-shadow 160ms ease,
    opacity 160ms ease;
}

.new-chat:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 14px 26px rgba(16, 156, 137, 0.26);
}

.new-chat:active:not(:disabled) {
  transform: translateY(0);
}

.new-chat:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.sidebar-scroll {
  min-height: 0;
  flex: 1;
  overflow-y: auto;
  padding: 2px 14px 18px;
}

.section + .section {
  margin-top: 22px;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 0 4px 8px;
}

.section-title {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.refresh-button {
  width: 28px;
  height: 28px;
}

.session-list {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.session-item {
  display: flex;
  align-items: center;
  border: 1px solid transparent;
  border-radius: 12px;
  transition:
    background 150ms ease,
    border-color 150ms ease;
}

.session-item:hover {
  background: rgba(238, 245, 243, 0.85);
}

.session-item.is-active {
  border-color: rgba(16, 156, 137, 0.16);
  background: var(--brand-soft);
}

.session-item.is-disabled {
  opacity: 0.62;
}

.session-main {
  display: flex;
  min-width: 0;
  flex: 1;
  align-items: center;
  gap: 10px;
  padding: 10px 8px 10px 12px;
  border: 0;
  background: transparent;
  cursor: pointer;
  text-align: left;
}

.session-indicator {
  width: 6px;
  height: 6px;
  flex: 0 0 auto;
  border-radius: 999px;
  background: #c6d8d3;
  transition: background 150ms ease;
}

.session-item.is-active .session-indicator {
  background: var(--brand);
  box-shadow: 0 0 0 4px rgba(16, 156, 137, 0.12);
}

.session-copy {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  gap: 2px;
}

.session-title {
  overflow: hidden;
  color: var(--text);
  font-size: 13px;
  font-weight: 550;
  line-height: 1.45;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-meta {
  overflow: hidden;
  color: var(--text-muted);
  font-size: 11px;
  line-height: 1.4;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-delete {
  width: 28px;
  height: 28px;
  margin-right: 4px;
  opacity: 0;
  color: var(--text-muted);
}

.session-item:hover .session-delete,
.session-item:focus-within .session-delete {
  opacity: 1;
}

.session-delete:hover {
  border-color: rgba(217, 82, 82, 0.16);
  background: var(--danger-soft);
  color: var(--danger);
}

.empty-sessions {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 20px 12px;
  border: 1px dashed var(--border);
  border-radius: 12px;
  color: var(--text-muted);
  text-align: center;
}

.empty-sessions p {
  margin: 4px 0 0;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 600;
}

.empty-sessions span {
  font-size: 11px;
}

.empty-sessions.is-loading > svg {
  color: var(--brand);
}

.empty-sessions.is-error {
  border-color: rgba(217, 82, 82, 0.2);
  background: rgba(253, 236, 236, 0.45);
}

.empty-sessions.is-error > svg {
  color: var(--danger);
}

.empty-sessions.is-error p {
  color: #b33f3f;
}

.retry-button {
  margin-top: 4px;
  padding: 4px 10px;
  border: 1px solid rgba(217, 82, 82, 0.22);
  border-radius: 7px;
  background: var(--surface);
  color: var(--danger);
  cursor: pointer;
  font-size: 10.5px;
  font-weight: 650;
  transition:
    background 150ms ease,
    border-color 150ms ease;
}

.retry-button:hover {
  border-color: rgba(217, 82, 82, 0.35);
  background: var(--danger-soft);
}

.example-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.example-item {
  display: flex;
  width: 100%;
  align-items: flex-start;
  gap: 9px;
  padding: 9px 10px;
  border: 1px solid transparent;
  border-radius: 11px;
  background: transparent;
  cursor: pointer;
  text-align: left;
  transition:
    background 150ms ease,
    border-color 150ms ease;
}

.example-item:hover:not(:disabled) {
  border-color: rgba(16, 156, 137, 0.13);
  background: rgba(248, 251, 250, 0.95);
}

.example-item:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.example-icon {
  display: grid;
  width: 26px;
  height: 26px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 8px;
  background: var(--surface-tint);
  color: var(--brand-deep);
}

.example-copy {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 1px;
}

.example-label {
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: 650;
}

.example-text {
  display: -webkit-box;
  overflow: hidden;
  color: var(--text-muted);
  font-size: 12px;
  line-height: 1.5;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.sidebar-foot {
  padding: 14px 18px 18px;
  border-top: 1px solid rgba(226, 236, 233, 0.8);
}

.service-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--surface-soft);
}

.service-dot {
  width: 8px;
  height: 8px;
  flex: 0 0 auto;
  border-radius: 999px;
  background: #b8c9c5;
}

.service-dot.is-ready {
  background: var(--brand);
  box-shadow: 0 0 0 4px rgba(16, 156, 137, 0.1);
}

.service-dot.is-busy {
  background: var(--amber);
  box-shadow: 0 0 0 4px rgba(217, 139, 22, 0.12);
  animation: pulse-soft 1.4s ease-in-out infinite;
}

.service-dot.is-error {
  background: var(--danger);
  box-shadow: 0 0 0 4px rgba(217, 82, 82, 0.1);
}

.service-copy {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  line-height: 1.35;
}

.service-copy strong {
  font-size: 12px;
  font-weight: 650;
}

.service-copy span {
  overflow: hidden;
  color: var(--text-muted);
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.service-icon {
  color: var(--text-muted);
}

.user-card {
  display: flex;
  align-items: center;
  gap: 9px;
  margin-top: 8px;
  padding: 9px 10px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--surface);
}

.user-avatar {
  display: grid;
  width: 30px;
  height: 30px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 9px;
  background: linear-gradient(135deg, #18b7a2, #4d8df7);
  color: #fff;
  font-size: 12px;
  font-weight: 700;
}

.user-copy {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  line-height: 1.35;
}

.user-copy strong {
  overflow: hidden;
  font-size: 11.5px;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-copy span {
  overflow: hidden;
  color: var(--text-muted);
  font-size: 10px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.logout-button {
  width: 28px;
  height: 28px;
  color: var(--text-muted);
}

.logout-button:hover {
  border-color: rgba(217, 82, 82, 0.16);
  background: var(--danger-soft);
  color: var(--danger);
}

.foot-note {
  margin: 9px 0 0;
  color: var(--text-muted);
  font-size: 10px;
  letter-spacing: 0.02em;
  text-align: center;
}

@media (max-width: 1024px) {
  .sidebar {
    position: fixed;
    inset: 0 auto 0 0;
    z-index: 50;
    width: min(86vw, 320px);
    min-width: 0;
    transform: translateX(-102%);
    transition: transform 220ms ease;
  }

  .sidebar--open {
    transform: translateX(0);
  }

  .sidebar-close {
    display: inline-grid;
  }
}

@media (hover: none) {
  .session-delete {
    opacity: 0.8;
  }
}
</style>
