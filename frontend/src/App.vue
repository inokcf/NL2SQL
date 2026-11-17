<script setup lang="ts">
import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
  watch,
} from "vue";
import { LoaderCircle, Sparkles, X } from "lucide-vue-next";

import AppSidebar from "./components/AppSidebar.vue";
import AuthView from "./components/AuthView.vue";
import ChatHeader from "./components/ChatHeader.vue";
import ComposerBar from "./components/ComposerBar.vue";
import ConfirmDialog from "./components/ConfirmDialog.vue";
import EmptyState from "./components/EmptyState.vue";
import MemoryDrawer from "./components/MemoryDrawer.vue";
import MessageItem from "./components/MessageItem.vue";
import { useAuth } from "./composables/useAuth";
import { useChat } from "./composables/useChat";
import { AUTH_EXPIRED_EVENT } from "./lib/apiBase";
import { examplePrompts } from "./lib/examples";
import type { SessionInfo } from "./types/agent";

const {
  messages,
  draft,
  sessionId,
  sessions,
  memories,
  isStreaming,
  memoryLoading,
  sessionsLoading,
  sessionsError,
  serviceState,
  notice,
  activeSession,
  startQuery,
  stopQuery,
  newChat,
  resetAll,
  selectSession,
  deleteSessionById,
  refreshSessions,
  loadMemories,
  pushNotice,
  clearNotice,
} = useChat();

const {
  user,
  isAuthenticated,
  initialized,
  initialize,
  logout,
  expire,
} = useAuth();

const sidebarOpen = ref(false);
const memoryOpen = ref(false);
const confirmTarget = ref<SessionInfo | null>(null);
const scrollEl = ref<HTMLElement | null>(null);
const composerRef = ref<{ focus: () => void } | null>(null);

const canSend = computed(
  () => draft.value.trim().length > 0 && !isStreaming.value,
);

const showEmpty = computed(() => messages.value.length === 0);

const headerTitle = computed(() => {
  if (activeSession.value?.title) return activeSession.value.title;
  const firstQuestion = messages.value.find(
    (message) => message.role === "user",
  );
  return firstQuestion?.content || "新的对话";
});

const headerSubtitle = computed(() =>
  sessionId.value
    ? "多轮对话已开启，可以继续追问"
    : "混合检索 · 多轮记忆 · SQL 闭环",
);

const confirmMessage = computed(() =>
  confirmTarget.value
    ? `确定删除「${confirmTarget.value.title}」吗？该会话的短期消息和长期记忆会一并删除。`
    : "",
);

async function scrollToBottom() {
  await nextTick();
  const element = scrollEl.value;
  if (!element) return;

  // 空状态通常比移动端视口更高，此时应回到顶部展示标题而不是滚到底部
  if (messages.value.length === 0) {
    element.scrollTo({ top: 0, behavior: "auto" });
    return;
  }

  element.scrollTo({
    top: element.scrollHeight,
    behavior: isStreaming.value ? "auto" : "smooth",
  });
}

watch(messages, scrollToBottom, { deep: true });

watch(isAuthenticated, async (authenticated, previous) => {
  if (!authenticated) {
    resetAll();
    sidebarOpen.value = false;
    memoryOpen.value = false;
    confirmTarget.value = null;
    return;
  }

  if (!previous) {
    resetAll();
    sidebarOpen.value = false;
    memoryOpen.value = false;
    await refreshSessions(true);
  }
});

function handleAuthExpired() {
  expire();
}

onMounted(async () => {
  window.addEventListener(AUTH_EXPIRED_EVENT, handleAuthExpired);
  await initialize();
});

onBeforeUnmount(() => {
  window.removeEventListener(AUTH_EXPIRED_EVENT, handleAuthExpired);
});

function handleLogout() {
  logout();
}

function handleNewChat() {
  if (isStreaming.value) return;
  newChat();
  memoryOpen.value = false;
  sidebarOpen.value = false;
  nextTick(() => composerRef.value?.focus());
}

function handleUseExample(text: string) {
  draft.value = text;
  sidebarOpen.value = false;
  nextTick(() => composerRef.value?.focus());
}

async function handleSelectSession(targetSessionId: string) {
  if (isStreaming.value) return;
  await selectSession(targetSessionId);
  sidebarOpen.value = false;
}

function handleDeleteSession(session: SessionInfo) {
  confirmTarget.value = session;
}

async function confirmDelete() {
  const target = confirmTarget.value;
  if (!target) return;
  const deleted = await deleteSessionById(target.session_id);
  confirmTarget.value = null;
  if (deleted) memoryOpen.value = false;
}

function openMemory() {
  if (!sessionId.value) {
    pushNotice("info", "先进行一次问数，才能查看当前会话记忆");
    return;
  }
  memoryOpen.value = true;
  loadMemories();
}

function handleRefreshSessions() {
  refreshSessions(false);
}
</script>

<template>
  <div v-if="!initialized" class="boot-screen">
    <div class="boot-brand">
      <span class="boot-logo" aria-hidden="true">
        <Sparkles :size="20" />
      </span>
      <div class="boot-copy">
        <strong>AI问数</strong>
        <span>NL2SQL Agent</span>
      </div>
    </div>
    <span class="boot-loading">
      <LoaderCircle class="spin" :size="14" />
      正在恢复登录状态…
    </span>
  </div>

  <AuthView v-else-if="!isAuthenticated" />

  <div v-else class="app-shell">
    <div class="ambient ambient--mint" aria-hidden="true" />
    <div class="ambient ambient--sky" aria-hidden="true" />

    <div
      v-if="sidebarOpen"
      class="sidebar-scrim"
      aria-hidden="true"
      @click="sidebarOpen = false"
    />

    <AppSidebar
      :class="{ 'sidebar--open': sidebarOpen }"
      :sessions="sessions"
      :active-session-id="sessionId"
      :is-streaming="isStreaming"
      :sessions-loading="sessionsLoading"
      :sessions-error="sessionsError"
      :service-state="serviceState"
      :user="user"
      :examples="examplePrompts"
      @new-chat="handleNewChat"
      @select-session="handleSelectSession"
      @delete-session="handleDeleteSession"
      @use-example="handleUseExample"
      @refresh="handleRefreshSessions"
      @close="sidebarOpen = false"
      @logout="handleLogout"
    />

    <main class="main-panel">
      <ChatHeader
        :title="headerTitle"
        :subtitle="headerSubtitle"
        :is-streaming="isStreaming"
        :session-id="sessionId"
        :service-state="serviceState"
        @toggle-sidebar="sidebarOpen = true"
        @open-memory="openMemory"
        @new-chat="handleNewChat"
      />

      <div ref="scrollEl" class="chat-scroll">
        <EmptyState
          v-if="showEmpty"
          :examples="examplePrompts"
          @use="handleUseExample"
        />

        <div v-else class="message-list">
          <MessageItem
            v-for="message in messages"
            :key="message.id"
            :message="message"
          />

          <div class="conversation-end">
            <span aria-hidden="true" />
            {{ isStreaming ? "正在分析中" : "本次分析结束" }}
            <span aria-hidden="true" />
          </div>
        </div>
      </div>

      <div class="composer-dock">
        <ComposerBar
          ref="composerRef"
          v-model="draft"
          :streaming="isStreaming"
          :can-send="canSend"
          @submit="startQuery()"
          @stop="stopQuery"
        />
        <p class="disclaimer">
          AI 生成内容仅供参考，请核对关键数据与业务口径。
        </p>
      </div>
    </main>

    <MemoryDrawer
      :open="memoryOpen"
      :loading="memoryLoading"
      :memories="memories"
      :session-title="headerTitle"
      @close="memoryOpen = false"
      @refresh="loadMemories"
    />

    <ConfirmDialog
      :open="Boolean(confirmTarget)"
      title="删除这个会话？"
      :message="confirmMessage"
      confirm-text="删除会话"
      danger
      @confirm="confirmDelete"
      @cancel="confirmTarget = null"
    />

    <Transition name="toast">
      <div
        v-if="notice"
        class="toast"
        :class="`is-${notice.type}`"
        role="status"
        @click="clearNotice"
      >
        <span class="toast-dot" aria-hidden="true" />
        <span class="toast-text">{{ notice.message }}</span>
        <button
          type="button"
          class="toast-close"
          aria-label="关闭提示"
          @click.stop="clearNotice"
        >
          <X :size="13" />
        </button>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.boot-screen {
  display: flex;
  height: 100dvh;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 18px;
  background:
    radial-gradient(circle at 30% 20%, rgba(16, 156, 137, 0.12), transparent 34%),
    radial-gradient(circle at 78% 12%, rgba(77, 141, 247, 0.1), transparent 28%),
    var(--bg);
}

.boot-brand {
  display: flex;
  align-items: center;
  gap: 11px;
}

.boot-logo {
  display: grid;
  width: 42px;
  height: 42px;
  place-items: center;
  border-radius: 13px;
  background: linear-gradient(135deg, #18b7a2, #0b897a);
  box-shadow: 0 8px 18px rgba(16, 156, 137, 0.24);
  color: #fff;
}

.boot-copy {
  display: flex;
  flex-direction: column;
  line-height: 1.3;
}

.boot-copy strong {
  font-size: 16px;
  font-weight: 700;
}

.boot-copy span {
  color: var(--text-muted);
  font-size: 10.5px;
  letter-spacing: 0.08em;
}

.boot-loading {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: var(--text-muted);
  font-size: 11px;
}

.app-shell {
  position: relative;
  display: grid;
  height: 100dvh;
  grid-template-columns: 292px minmax(0, 1fr);
  overflow: hidden;
}

.ambient {
  position: fixed;
  z-index: 0;
  border-radius: 999px;
  filter: blur(80px);
  pointer-events: none;
}

.ambient--mint {
  top: -140px;
  left: 6%;
  width: 420px;
  height: 420px;
  background: rgba(30, 190, 166, 0.12);
}

.ambient--sky {
  top: -180px;
  right: 4%;
  width: 460px;
  height: 460px;
  background: rgba(77, 141, 247, 0.1);
}

.main-panel {
  position: relative;
  z-index: 1;
  display: flex;
  min-width: 0;
  height: 100dvh;
  flex-direction: column;
  overflow: hidden;
}

.chat-scroll {
  min-height: 0;
  flex: 1;
  overflow-y: auto;
  overscroll-behavior: contain;
  overflow-anchor: none;
}

.message-list {
  display: flex;
  width: 100%;
  max-width: 1000px;
  flex-direction: column;
  gap: 24px;
  margin: 0 auto;
  padding: 30px 28px 16px;
}

.conversation-end {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 4px;
  color: var(--text-muted);
  font-size: 9.5px;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-align: center;
  text-transform: uppercase;
}

.conversation-end span {
  height: 1px;
  flex: 1;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(210, 226, 221, 0.9),
    transparent
  );
}

.composer-dock {
  position: relative;
  z-index: 5;
  flex: 0 0 auto;
  padding: 14px 24px 10px;
  background: linear-gradient(
    to top,
    rgba(244, 249, 247, 0.99) 54%,
    rgba(244, 249, 247, 0.82) 78%,
    rgba(244, 249, 247, 0)
  );
}

.disclaimer {
  margin: 7px 0 0;
  color: var(--text-muted);
  font-size: 9.5px;
  letter-spacing: 0.02em;
  text-align: center;
}

.sidebar-scrim {
  display: none;
}

.toast {
  position: fixed;
  top: 18px;
  left: 50%;
  z-index: 140;
  display: flex;
  max-width: min(440px, 92vw);
  align-items: center;
  gap: 9px;
  padding: 9px 10px 9px 12px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.97);
  box-shadow: var(--shadow-lg);
  color: var(--text);
  cursor: pointer;
  transform: translateX(-50%);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
}

.toast-dot {
  width: 7px;
  height: 7px;
  flex: 0 0 auto;
  border-radius: 999px;
  background: var(--sky);
}

.toast.is-success {
  border-color: rgba(16, 156, 137, 0.2);
}

.toast.is-success .toast-dot {
  background: var(--brand);
}

.toast.is-error {
  border-color: rgba(217, 82, 82, 0.2);
}

.toast.is-error .toast-dot {
  background: var(--danger);
}

.toast.is-info {
  border-color: rgba(77, 141, 247, 0.18);
}

.toast-text {
  flex: 1;
  font-size: 11.5px;
  line-height: 1.5;
}

.toast-close {
  display: grid;
  width: 24px;
  height: 24px;
  flex: 0 0 auto;
  place-items: center;
  border: 0;
  border-radius: 7px;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
}

.toast-close:hover {
  background: var(--surface-muted);
  color: var(--text);
}

.toast-enter-active,
.toast-leave-active {
  transition:
    opacity 180ms ease,
    transform 180ms ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translate(-50%, -8px);
}

@media (max-width: 1024px) {
  .app-shell {
    grid-template-columns: minmax(0, 1fr);
  }

  .sidebar-scrim {
    position: fixed;
    inset: 0;
    z-index: 40;
    display: block;
    background: rgba(12, 33, 30, 0.3);
    backdrop-filter: blur(2px);
    -webkit-backdrop-filter: blur(2px);
  }
}

@media (max-width: 640px) {
  .message-list {
    gap: 20px;
    padding: 20px 14px 12px;
  }

  .composer-dock {
    padding: 10px 12px 8px;
  }
}
</style>
