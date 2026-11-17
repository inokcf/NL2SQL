<script setup lang="ts">
import { computed } from "vue";
import {
  Brain,
  History,
  LoaderCircle,
  RefreshCw,
  Sparkles,
  X,
} from "lucide-vue-next";

import { relativeTime } from "../lib/format";
import type { MemoryItem } from "../types/agent";

const props = defineProps<{
  open: boolean;
  loading: boolean;
  memories: MemoryItem[];
  sessionTitle: string;
}>();

const emit = defineEmits<{
  (event: "close"): void;
  (event: "refresh"): void;
}>();

const semanticMemories = computed(() =>
  props.memories
    .filter((memory) => memory.memory_type === "semantic")
    .sort((a, b) => b.created_at.localeCompare(a.created_at)),
);

const episodicMemories = computed(() =>
  props.memories
    .filter((memory) => memory.memory_type !== "semantic")
    .sort((a, b) => b.created_at.localeCompare(a.created_at)),
);
</script>

<template>
  <Teleport to="body">
    <Transition name="drawer">
      <div
        v-if="open"
        class="drawer-root"
        role="dialog"
        aria-modal="true"
        aria-label="长期记忆"
        @click.self="emit('close')"
      >
        <aside class="drawer-panel">
          <header class="drawer-head">
            <span class="drawer-icon" aria-hidden="true">
              <Brain :size="19" />
            </span>
            <div class="drawer-title">
              <strong>长期记忆</strong>
              <span>当前会话 · {{ sessionTitle }}</span>
            </div>
            <button
              type="button"
              class="icon-button"
              aria-label="关闭记忆面板"
              @click="emit('close')"
            >
              <X :size="18" />
            </button>
          </header>

          <div class="drawer-toolbar">
            <span class="memory-count">
              共 {{ memories.length }} 条向量记忆
            </span>
            <button
              type="button"
              class="refresh-button"
              :disabled="loading"
              @click="emit('refresh')"
            >
              <LoaderCircle v-if="loading" class="spin" :size="13" />
              <RefreshCw v-else :size="13" />
              刷新
            </button>
          </div>

          <div class="drawer-body">
            <div v-if="loading" class="loading-state">
              <LoaderCircle class="spin" :size="22" />
              <p>正在加载记忆…</p>
            </div>

            <div v-else-if="!memories.length" class="empty-state">
              <span class="empty-icon" aria-hidden="true">
                <Brain :size="24" />
              </span>
              <strong>还没有长期记忆</strong>
              <p>
                完成一次问数后，系统会把可复用的用户偏好和问数记录写入向量库。
              </p>
            </div>

            <template v-else>
              <section v-if="semanticMemories.length" class="memory-section">
                <div class="section-head">
                  <span class="section-title">
                    <Sparkles :size="14" />
                    长期偏好
                  </span>
                  <span class="section-count">{{ semanticMemories.length }}</span>
                </div>
                <article
                  v-for="memory in semanticMemories"
                  :key="memory.id"
                  class="memory-card is-semantic"
                >
                  <div class="memory-card-head">
                    <span class="memory-badge is-semantic">偏好</span>
                    <span class="memory-time">
                      {{ relativeTime(memory.created_at) }}
                    </span>
                  </div>
                  <p class="memory-content">{{ memory.content }}</p>
                </article>
              </section>

              <section v-if="episodicMemories.length" class="memory-section">
                <div class="section-head">
                  <span class="section-title">
                    <History :size="14" />
                    问数记录
                  </span>
                  <span class="section-count">{{ episodicMemories.length }}</span>
                </div>
                <article
                  v-for="memory in episodicMemories"
                  :key="memory.id"
                  class="memory-card"
                >
                  <div class="memory-card-head">
                    <span class="memory-badge">记录</span>
                    <span class="memory-time">
                      {{ relativeTime(memory.created_at) }}
                    </span>
                  </div>
                  <p class="memory-content">{{ memory.content }}</p>
                </article>
              </section>
            </template>
          </div>

          <footer class="drawer-foot">
            记忆按用户隔离，并在 SQL 生成前通过语义检索注入提示词。
          </footer>
        </aside>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.drawer-root {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: flex;
  justify-content: flex-end;
  background: rgba(12, 33, 30, 0.3);
  backdrop-filter: blur(2px);
  -webkit-backdrop-filter: blur(2px);
}

.drawer-panel {
  display: flex;
  width: min(440px, 94vw);
  height: 100%;
  flex-direction: column;
  border-left: 1px solid var(--border);
  background: var(--surface);
  box-shadow: -24px 0 60px rgba(23, 50, 46, 0.16);
  animation: drawer-in 220ms ease both;
}

.drawer-head {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 18px 18px 15px;
  border-bottom: 1px solid var(--border);
}

.drawer-icon {
  display: grid;
  width: 38px;
  height: 38px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 12px;
  background: linear-gradient(145deg, var(--brand-soft), #eef3ff);
  color: var(--brand-deep);
}

.drawer-title {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  line-height: 1.4;
}

.drawer-title strong {
  font-size: 15px;
  font-weight: 700;
}

.drawer-title span {
  overflow: hidden;
  color: var(--text-muted);
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.drawer-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 18px;
  border-bottom: 1px solid rgba(226, 236, 233, 0.7);
  background: var(--surface-soft);
}

.memory-count {
  color: var(--text-muted);
  font-size: 10.5px;
}

.refresh-button {
  display: inline-flex;
  height: 27px;
  align-items: center;
  gap: 5px;
  padding: 0 9px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--surface);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 10.5px;
  font-weight: 600;
}

.refresh-button:hover:not(:disabled) {
  border-color: rgba(16, 156, 137, 0.22);
  color: var(--brand-deep);
}

.refresh-button:disabled {
  cursor: wait;
  opacity: 0.6;
}

.drawer-body {
  min-height: 0;
  flex: 1;
  overflow-y: auto;
  padding: 16px 18px 20px;
}

.loading-state,
.empty-state {
  display: flex;
  height: 100%;
  min-height: 260px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--text-muted);
  text-align: center;
}

.loading-state svg {
  color: var(--brand);
}

.loading-state p,
.empty-state p {
  max-width: 260px;
  margin: 0;
  font-size: 11.5px;
  line-height: 1.7;
}

.empty-icon {
  display: grid;
  width: 52px;
  height: 52px;
  margin-bottom: 2px;
  place-items: center;
  border-radius: 16px;
  background: var(--brand-soft);
  color: var(--brand-deep);
}

.empty-state strong {
  color: var(--text);
  font-size: 13px;
}

.memory-section + .memory-section {
  margin-top: 22px;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 9px;
  padding: 0 2px;
}

.section-title {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.section-title svg {
  color: var(--brand);
}

.section-count {
  min-width: 20px;
  padding: 1px 6px;
  border-radius: 999px;
  background: var(--surface-muted);
  color: var(--text-muted);
  font-size: 9.5px;
  text-align: center;
}

.memory-card {
  padding: 11px 12px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--surface-soft);
}

.memory-card + .memory-card {
  margin-top: 7px;
}

.memory-card.is-semantic {
  border-color: rgba(16, 156, 137, 0.14);
  background: rgba(225, 245, 240, 0.44);
}

.memory-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 6px;
}

.memory-badge {
  padding: 1px 6px;
  border-radius: 999px;
  background: var(--surface-muted);
  color: var(--text-muted);
  font-size: 9px;
  font-weight: 650;
}

.memory-badge.is-semantic {
  background: var(--brand-soft);
  color: var(--brand-deep);
}

.memory-time {
  color: var(--text-muted);
  font-size: 9.5px;
}

.memory-content {
  max-height: 190px;
  overflow-y: auto;
  margin: 0;
  color: var(--text-secondary);
  font-size: 11.5px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}

.drawer-foot {
  padding: 12px 18px 16px;
  border-top: 1px solid var(--border);
  color: var(--text-muted);
  font-size: 9.5px;
  line-height: 1.6;
  text-align: center;
}

.drawer-enter-active,
.drawer-leave-active {
  transition: opacity 180ms ease;
}

.drawer-enter-from,
.drawer-leave-to {
  opacity: 0;
}

@keyframes drawer-in {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}
</style>
