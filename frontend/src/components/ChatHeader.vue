<script setup lang="ts">
import { computed } from "vue";
import { Brain, Menu, Plus } from "lucide-vue-next";

import type { ServiceState } from "../types/agent";

const props = defineProps<{
  title: string;
  subtitle: string;
  isStreaming: boolean;
  sessionId: string | null;
  serviceState: ServiceState;
}>();

const statusText = computed(() => {
  if (props.isStreaming) return "正在分析";
  if (props.serviceState === "error") return "连接异常";
  return "服务就绪";
});

const statusClass = computed(() =>
  props.isStreaming ? "is-live" : `is-${props.serviceState}`,
);

const emit = defineEmits<{
  (event: "toggle-sidebar"): void;
  (event: "open-memory"): void;
  (event: "new-chat"): void;
}>();
</script>

<template>
  <header class="chat-header">
    <div class="header-left">
      <button
        type="button"
        class="icon-button menu-button"
        aria-label="打开侧边栏"
        @click="emit('toggle-sidebar')"
      >
        <Menu :size="19" />
      </button>

      <div class="title-block">
        <span class="eyebrow">数据分析工作台</span>
        <h1 :title="title">{{ title }}</h1>
        <p>{{ subtitle }}</p>
      </div>
    </div>

    <div class="header-actions">
      <span class="status-pill" :class="statusClass">
        <span class="status-dot" aria-hidden="true" />
        {{ statusText }}
      </span>

      <button
        type="button"
        class="ghost-button"
        :disabled="!sessionId"
        title="查看长期记忆"
        @click="emit('open-memory')"
      >
        <Brain :size="16" />
        <span>记忆</span>
      </button>

      <button
        type="button"
        class="ghost-button primary"
        :disabled="isStreaming"
        @click="emit('new-chat')"
      >
        <Plus :size="16" />
        <span>新对话</span>
      </button>
    </div>
  </header>
</template>

<style scoped>
.chat-header {
  position: relative;
  z-index: 10;
  display: flex;
  min-height: 78px;
  flex: 0 0 auto;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 14px 26px;
  border-bottom: 1px solid rgba(226, 236, 233, 0.78);
  background: rgba(244, 249, 247, 0.76);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
}

.header-left {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 12px;
}

.menu-button {
  display: none;
}

.title-block {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 1px;
}

.eyebrow {
  color: var(--brand-deep);
  font-size: 10px;
  font-weight: 750;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.title-block h1 {
  max-width: 540px;
  overflow: hidden;
  margin: 0;
  color: var(--text);
  font-size: 17px;
  font-weight: 700;
  letter-spacing: -0.01em;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.title-block p {
  max-width: 560px;
  overflow: hidden;
  margin: 1px 0 0;
  color: var(--text-muted);
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.header-actions {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 8px;
}

.status-pill {
  display: inline-flex;
  height: 32px;
  align-items: center;
  gap: 7px;
  padding: 0 11px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.7);
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: var(--brand);
  box-shadow: 0 0 0 3px rgba(16, 156, 137, 0.1);
}

.status-pill.is-live {
  border-color: rgba(217, 139, 22, 0.2);
  background: var(--amber-soft);
  color: #97620e;
}

.status-pill.is-live .status-dot {
  background: var(--amber);
  box-shadow: 0 0 0 3px rgba(217, 139, 22, 0.14);
  animation: pulse-soft 1.3s ease-in-out infinite;
}

.status-pill.is-error {
  border-color: rgba(217, 82, 82, 0.18);
  background: var(--danger-soft);
  color: #b33f3f;
}

.status-pill.is-error .status-dot {
  background: var(--danger);
  box-shadow: 0 0 0 3px rgba(217, 82, 82, 0.1);
}

.ghost-button {
  display: inline-flex;
  height: 34px;
  align-items: center;
  gap: 6px;
  padding: 0 12px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.72);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  transition:
    background 160ms ease,
    border-color 160ms ease,
    color 160ms ease,
    transform 160ms ease;
}

.ghost-button:hover:not(:disabled) {
  border-color: rgba(16, 156, 137, 0.24);
  background: var(--surface);
  color: var(--brand-deep);
}

.ghost-button:active:not(:disabled) {
  transform: translateY(1px);
}

.ghost-button:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.ghost-button.primary {
  border-color: transparent;
  background: var(--brand-soft);
  color: var(--brand-deep);
}

.ghost-button.primary:hover:not(:disabled) {
  border-color: rgba(16, 156, 137, 0.2);
  background: #d9f2ec;
}

@media (max-width: 1024px) {
  .chat-header {
    padding: 12px 16px;
  }

  .menu-button {
    display: inline-grid;
  }
}

@media (max-width: 720px) {
  .status-pill,
  .ghost-button span {
    display: none;
  }

  .ghost-button {
    width: 34px;
    justify-content: center;
    padding: 0;
  }

  .title-block h1 {
    max-width: 42vw;
    font-size: 15px;
  }

  .title-block p {
    max-width: 46vw;
  }
}
</style>
